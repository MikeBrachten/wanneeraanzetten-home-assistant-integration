"""UI account linking, two-step verification, and reauthentication."""

from typing import Any

import voluptuous as vol
from homeassistant import config_entries
from homeassistant.const import CONF_ACCESS_TOKEN, CONF_EMAIL, CONF_PASSWORD
from homeassistant.core import callback
from homeassistant.helpers.aiohttp_client import async_get_clientsession
from homeassistant.helpers.selector import (
    SelectSelector,
    SelectSelectorConfig,
    TextSelector,
    TextSelectorConfig,
    TextSelectorType,
)

from .api import (
    CannotConnect,
    InvalidAuth,
    WanneerAanzettenApi,
    async_complete_two_factor,
    async_link,
)
from .const import (
    CONF_COUNTRY,
    CONF_RESOLUTION,
    COUNTRIES,
    DOMAIN,
    RESOLUTION_ACCOUNT,
)


class WanneerAanzettenConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Store only a scoped token; never store the account password."""

    VERSION = 1

    def __init__(self) -> None:
        self._pending_token: str | None = None
        self._country = "NL"
        self._email = ""

    async def async_step_user(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            self._country = user_input[CONF_COUNTRY]
            self._email = user_input[CONF_EMAIL]
            try:
                result = await async_link(self._email, user_input[CONF_PASSWORD])
                if "pending_token" in result:
                    self._pending_token = result["pending_token"]
                    return await self.async_step_two_factor()
                return await self._async_finish(result)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="user",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required(CONF_EMAIL, default=self._email): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.EMAIL)
                    ),
                    vol.Required(CONF_PASSWORD): TextSelector(
                        TextSelectorConfig(type=TextSelectorType.PASSWORD)
                    ),
                    vol.Required(CONF_COUNTRY, default=self._country): SelectSelector(
                        SelectSelectorConfig(options=COUNTRIES)
                    ),
                }
            ),
        )

    async def async_step_two_factor(self, user_input: dict[str, Any] | None = None):
        errors = {}
        if user_input is not None:
            try:
                result = await async_complete_two_factor(
                    self._pending_token, user_input["code"], user_input["recovery"]
                )
                self._pending_token = None
                return await self._async_finish(result)
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except CannotConnect:
                errors["base"] = "cannot_connect"
        return self.async_show_form(
            step_id="two_factor",
            errors=errors,
            data_schema=vol.Schema(
                {
                    vol.Required("code"): str,
                    vol.Required("recovery", default=False): bool,
                }
            ),
        )

    async def _async_revoke(self, token: str) -> None:
        try:
            await WanneerAanzettenApi(async_get_clientsession(self.hass), token).async_revoke()
        except (CannotConnect, InvalidAuth):
            pass

    async def _async_finish(self, result: dict):
        account_id = result["user"]["id"]
        data = {
            CONF_ACCESS_TOKEN: result["token"],
            CONF_EMAIL: result["user"]["email"],
            CONF_COUNTRY: self._country,
        }
        if self.source == config_entries.SOURCE_REAUTH:
            entry = self._get_reauth_entry()
            if entry.unique_id != account_id:
                await self._async_revoke(result["token"])
                return self.async_abort(reason="wrong_account")
            await self._async_revoke(entry.data[CONF_ACCESS_TOKEN])
            return self.async_update_reload_and_abort(entry, data_updates=data)
        await self.async_set_unique_id(account_id)
        if self._async_current_entries() and any(
            entry.unique_id == account_id for entry in self._async_current_entries()
        ):
            await self._async_revoke(result["token"])
        self._abort_if_unique_id_configured()
        return self.async_create_entry(title=result["user"]["email"], data=data)

    async def async_step_reauth(self, entry_data: dict[str, Any]):
        self._email = entry_data[CONF_EMAIL]
        self._country = entry_data[CONF_COUNTRY]
        return await self.async_step_user()

    @staticmethod
    @callback
    def async_get_options_flow(config_entry):
        return WanneerAanzettenOptionsFlow()


class WanneerAanzettenOptionsFlow(config_entries.OptionsFlow):
    """Guide users through market and contract-price settings."""

    async def async_step_init(self, user_input: dict[str, Any] | None = None):
        return self.async_show_menu(step_id="init", menu_options=["market", "contract"])

    async def async_step_market(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            options = {**self.config_entry.options, **user_input}
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(
            step_id="market",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_COUNTRY,
                        default=self.config_entry.options.get(
                            CONF_COUNTRY, self.config_entry.data[CONF_COUNTRY]
                        ),
                    ): SelectSelector(SelectSelectorConfig(options=COUNTRIES)),
                }
            ),
        )

    async def async_step_contract(self, user_input: dict[str, Any] | None = None):
        if user_input is not None:
            options = {**self.config_entry.options, **user_input}
            return self.async_create_entry(title="", data=options)
        return self.async_show_form(
            step_id="contract",
            data_schema=vol.Schema(
                {
                    vol.Required(
                        CONF_RESOLUTION,
                        default=self.config_entry.options.get(CONF_RESOLUTION, RESOLUTION_ACCOUNT),
                    ): SelectSelector(
                        SelectSelectorConfig(
                            options=[RESOLUTION_ACCOUNT, "kwartier", "uur"],
                            translation_key="price_resolution",
                        )
                    ),
                }
            ),
        )
