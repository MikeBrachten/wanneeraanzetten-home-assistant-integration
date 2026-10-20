"""Exercise the Python client against a local fixture for the public API contract."""

from copy import deepcopy
from unittest.mock import patch

import pytest
from aiohttp import ClientSession, web
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from pytest_socket import socket_allow_hosts

from custom_components.wanneeraanzetten.api import (
    CannotConnect,
    InvalidAuth,
    WanneerAanzettenApi,
    async_complete_two_factor,
    async_link,
)

from .test_integration import STATE


@pytest.fixture
async def backend(aiohttp_server, socket_enabled):
    """Serve the public API contract locally, including actual cookie handling."""
    socket_allow_hosts(["127.0.0.1", "::1"])
    service = web.Application()
    sessions = {}
    tokens = {}
    counter = 0

    async def login(request):
        body = await request.json()
        if body.get("password") != "contract test password":
            return web.json_response({}, status=401)
        if body["email"] == "twofactor@example.nl":
            return web.json_response({"requires2fa": True, "pendingToken": "pending"})
        sessions["plain_session"] = "usr_plain"
        response = web.json_response({"user": {"id": "usr_plain"}})
        response.set_cookie("wa_session", "plain_session", httponly=True)
        return response

    async def two_factor(request):
        body = await request.json()
        if body.get("code") != "123456" or body.get("pendingToken") != "pending":
            return web.json_response({}, status=401)
        sessions["two_factor_session"] = "usr_2fa"
        response = web.json_response({"user": {"id": "usr_2fa"}})
        response.set_cookie("wa_session", "two_factor_session", httponly=True)
        return response

    async def create_token(request):
        nonlocal counter
        user_id = sessions.get(request.cookies.get("wa_session"))
        if not user_id:
            return web.json_response({}, status=401)
        counter += 1
        token = f"wa_ha_fixture_{counter}"
        tokens[token] = user_id
        return web.json_response(
            {"token": token, "user": {"id": user_id, "email": "fixture@example.nl"}}, status=201
        )

    async def logout(request):
        sessions.pop(request.cookies.get("wa_session"), None)
        return web.Response(status=204)

    async def state(request):
        user_id = tokens.get(request.headers.get("Authorization", "").removeprefix("Bearer "))
        if not user_id:
            return web.json_response({}, status=401)
        result = deepcopy(STATE)
        result["user"]["id"] = user_id
        assert not sessions, "Temporary login sessions must have been logged out"
        return web.json_response(result)

    async def revoke(request):
        token = request.headers.get("Authorization", "").removeprefix("Bearer ")
        if token not in tokens:
            return web.json_response({}, status=401)
        del tokens[token]
        return web.Response(status=204)

    service.router.add_post("/api/v1/auth/login", login)
    service.router.add_post("/api/v1/auth/2fa", two_factor)
    service.router.add_post("/api/v1/2fa/recovery", two_factor)
    service.router.add_post("/api/v1/home-assistant/tokens", create_token)
    service.router.add_post("/api/v1/auth/logout", logout)
    service.router.add_get("/api/v1/home-assistant/state", state)
    service.router.add_delete("/api/v1/home-assistant/token", revoke)
    server = await aiohttp_server(service)
    url = str(server.make_url("/")).rstrip("/").replace("127.0.0.1", "localhost")
    with patch("custom_components.wanneeraanzetten.api.BASE_URL", url):
        yield {"url": url, "code": "123456"}


async def test_real_login_cookie_exchange_snapshot_and_revoke(backend):
    result = await async_link("plain@example.nl", "contract test password")
    assert result["user"]["id"] == "usr_plain"
    assert result["token"].startswith("wa_ha_")
    async with ClientSession() as session:
        client = WanneerAanzettenApi(session, result["token"])
        state = await client.async_state("NL")
        assert state["price"]["value"] == -0.02
        assert state["devices"][0]["recommendedNow"] is True
        assert len(state["devices"]) == 1
        # Login cookies never entered the polling session.
        assert len(session.cookie_jar) == 0
        await client.async_revoke()
        with pytest.raises(InvalidAuth):
            await client.async_state("NL")


async def test_real_two_factor_exchange(backend):
    result = await async_link("twofactor@example.nl", "contract test password")
    assert "pending_token" in result
    with pytest.raises(InvalidAuth):
        await async_complete_two_factor(result["pending_token"], "wrong")
    result = await async_complete_two_factor(result["pending_token"], backend["code"])
    assert result["user"]["id"] == "usr_2fa"
    async with ClientSession() as session:
        await WanneerAanzettenApi(session, result["token"]).async_revoke()


async def test_real_invalid_password(backend):
    with pytest.raises(InvalidAuth):
        await async_link("plain@example.nl", "wrong")


@pytest.mark.parametrize("status", [302, 429, 500])
async def test_service_errors_are_not_auth_failures(hass, aioclient_mock, status):
    aioclient_mock.get(
        "https://wanneeraanzetten.nl/api/v1/home-assistant/state?country=NL", status=status
    )
    with pytest.raises(CannotConnect):
        await WanneerAanzettenApi(async_get_clientsession(hass), "token").async_state("NL")


async def test_invalid_response_is_a_transient_failure(hass, aioclient_mock):
    aioclient_mock.get(
        "https://wanneeraanzetten.nl/api/v1/home-assistant/state?country=NL", json={}
    )
    with pytest.raises(CannotConnect):
        await WanneerAanzettenApi(async_get_clientsession(hass), "token").async_state("NL")


@pytest.mark.parametrize("corruption", ["price", "recommendation"])
async def test_malformed_values_do_not_become_valid_entity_states(hass, aioclient_mock, corruption):
    response = deepcopy(STATE)
    if corruption == "price":
        response["price"]["value"] = "unknown"
    else:
        response["devices"][0]["recommendedNow"] = None
    aioclient_mock.get(
        "https://wanneeraanzetten.nl/api/v1/home-assistant/state?country=NL", json=response
    )
    with pytest.raises(CannotConnect):
        await WanneerAanzettenApi(async_get_clientsession(hass), "token").async_state("NL")
