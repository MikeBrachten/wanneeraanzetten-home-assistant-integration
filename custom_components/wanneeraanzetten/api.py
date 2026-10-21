"""Async client with isolated login cookies and scoped integration credentials."""

from __future__ import annotations

import asyncio
import math
from typing import Any

from aiohttp import ClientError, ClientSession, ClientTimeout

from .const import BASE_URL


class CannotConnect(Exception):
    """The service is unavailable or returned an invalid response."""


class InvalidAuth(Exception):
    """Credentials have expired or were rejected."""


async def _request(
    session: ClientSession, method: str, path: str, **kwargs: Any
) -> dict[str, Any]:
    try:
        async with session.request(
            method, f"{BASE_URL}/api/v1/{path}",
            timeout=ClientTimeout(total=20), allow_redirects=False, **kwargs
        ) as response:
            if response.status in (401, 403):
                raise InvalidAuth
            if response.status not in (200, 201, 204):
                raise CannotConnect(f"Service returned HTTP {response.status}")
            if response.status == 204:
                return {}
            result = await response.json()
            if not isinstance(result, dict):
                raise CannotConnect("Invalid service response")
            return result
    except (ClientError, asyncio.TimeoutError, ValueError) as err:
        raise CannotConnect("Unable to reach the service") from err


async def _finish_link(session: ClientSession) -> dict[str, Any]:
    try:
        result = await _request(session, "POST", "home-assistant/tokens", json={})
        user = result.get("user")
        if (
            not isinstance(result.get("token"), str)
            or not isinstance(user, dict)
            or not isinstance(user.get("id"), str)
            or not isinstance(user.get("email"), str)
        ):
            raise CannotConnect("Invalid account-link response")
        return result
    finally:
        try:
            await _request(session, "POST", "auth/logout", json={})
        except (CannotConnect, InvalidAuth):
            pass


async def async_link(email: str, password: str) -> dict[str, Any]:
    """Exchange a normal login for a token without retaining the password."""
    async with ClientSession() as session:
        result = await _request(
            session, "POST", "auth/login", json={"email": email, "password": password}
        )
        if result.get("requires2fa"):
            if not isinstance(result.get("pendingToken"), str):
                raise CannotConnect("Invalid two-step verification response")
            return {"pending_token": result["pendingToken"]}
        return await _finish_link(session)


async def async_complete_two_factor(
    pending_token: str, code: str, recovery: bool = False
) -> dict[str, Any]:
    """Complete the existing two-factor or one-time recovery-code flow."""
    async with ClientSession() as session:
        await _request(
            session, "POST", "2fa/recovery" if recovery else "auth/2fa",
            json={"pendingToken": pending_token, "code": code},
        )
        return await _finish_link(session)


class WanneerAanzettenApi:
    """Read prices and device recommendations using a scoped bearer token."""

    def __init__(self, session: ClientSession, token: str) -> None:
        self.session = session
        self.token = token

    async def async_state(self, country: str) -> dict[str, Any]:
        result = await _request(
            self.session, "GET", "home-assistant/state",
            headers={"Authorization": f"Bearer {self.token}"},
            params={"country": country},
        )
        try:
            if not isinstance(result["user"]["id"], str):
                raise ValueError
            price = result["price"]
            if not isinstance(price["available"], bool):
                raise ValueError
            if not {"value", "source", "start", "end"}.issubset(price):
                raise ValueError
            if price["available"] and (
                type(price["value"]) not in (int, float)
                or not math.isfinite(price["value"])
            ):
                raise ValueError
            if not isinstance(result["devices"], list):
                raise ValueError
            if "prices" in result and not isinstance(result["prices"], list):
                raise ValueError
            if "tariffPreferences" in result and result["tariffPreferences"] is not None and not isinstance(result["tariffPreferences"], dict):
                raise ValueError
            for item in result.get("prices", []):
                if not isinstance(item, dict) or not isinstance(item.get("start"), str) or not isinstance(item.get("end"), str):
                    raise ValueError
                if type(item.get("value")) not in (int, float) or not math.isfinite(item["value"]):
                    raise ValueError
            for device in result["devices"]:
                if not isinstance(device["id"], str) or not isinstance(device["available"], bool):
                    raise ValueError
                if not isinstance(device["name"], str):
                    raise ValueError
                if device["available"] and not isinstance(device["recommendedNow"], bool):
                    raise ValueError
        except (KeyError, TypeError, ValueError) as err:
            raise CannotConnect("Invalid state response") from err
        return result

    async def async_revoke(self) -> None:
        await _request(
            self.session, "DELETE", "home-assistant/token",
            headers={"Authorization": f"Bearer {self.token}"},
            json={},
        )
