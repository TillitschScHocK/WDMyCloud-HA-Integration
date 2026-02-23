"""Config flow for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.data_entry_flow import FlowResult

from .const import (
    DOMAIN,
    CONF_SNMP_VERSION,
    CONF_HOST,
    CONF_COMMUNITY,
    CONF_USERNAME,
    CONF_AUTH_PROTOCOL,
    CONF_AUTH_PASSWORD,
    CONF_PRIV_PROTOCOL,
    CONF_PRIV_PASSWORD,
    CONF_SCAN_INTERVAL,
    SNMP_VERSION_V2C,
    SNMP_VERSION_V3,
    AUTH_PROTOCOLS,
    PRIV_PROTOCOLS,
    SCAN_INTERVAL_OPTIONS,
    DEFAULT_SCAN_INTERVAL,
)
from .snmp_helper import (
    CannotConnect,
    InvalidAuth,
    SnmpLibraryMissing,
    sanitize_host,
    test_snmp_connection,
)

_LOGGER = logging.getLogger(__name__)


class WDEx2UltraConfigFlow(config_entries.ConfigFlow, domain=DOMAIN):
    """Handle a config flow for WD MyCloud EX2 Ultra."""

    VERSION = 1

    def __init__(self) -> None:
        """Initialize config flow."""
        self._snmp_version: str | None = None

    async def async_step_user(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 1: Select SNMP version."""
        if user_input is not None:
            self._snmp_version = user_input[CONF_SNMP_VERSION]
            if self._snmp_version == SNMP_VERSION_V2C:
                return await self.async_step_v2c()
            return await self.async_step_v3()

        schema = vol.Schema(
            {
                vol.Required(CONF_SNMP_VERSION, default=SNMP_VERSION_V2C): vol.In(
                    [SNMP_VERSION_V2C, SNMP_VERSION_V3]
                )
            }
        )
        return self.async_show_form(step_id="user", data_schema=schema)

    async def async_step_v2c(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2a: SNMPv2c credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            clean_host = sanitize_host(user_input[CONF_HOST])
            data = {
                CONF_SNMP_VERSION: SNMP_VERSION_V2C,
                CONF_HOST: clean_host,
                CONF_COMMUNITY: user_input.get(CONF_COMMUNITY, "public"),
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            }
            try:
                await test_snmp_connection(data)
            except SnmpLibraryMissing:
                errors["base"] = "snmp_library_missing"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during SNMPv2c setup")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"WD EX2 Ultra ({clean_host})",
                    data=data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Optional(CONF_COMMUNITY, default="public"): str,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.In(SCAN_INTERVAL_OPTIONS),
            }
        )
        return self.async_show_form(step_id="v2c", data_schema=schema, errors=errors)

    async def async_step_v3(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2b: SNMPv3 credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            clean_host = sanitize_host(user_input[CONF_HOST])
            data = {
                CONF_SNMP_VERSION: SNMP_VERSION_V3,
                CONF_HOST: clean_host,
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_AUTH_PROTOCOL: user_input[CONF_AUTH_PROTOCOL],
                CONF_AUTH_PASSWORD: user_input[CONF_AUTH_PASSWORD],
                CONF_PRIV_PROTOCOL: user_input[CONF_PRIV_PROTOCOL],
                CONF_PRIV_PASSWORD: user_input[CONF_PRIV_PASSWORD],
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            }
            try:
                await test_snmp_connection(data)
            except SnmpLibraryMissing:
                errors["base"] = "snmp_library_missing"
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:
                _LOGGER.exception("Unexpected error during SNMPv3 setup")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"WD EX2 Ultra ({clean_host})",
                    data=data,
                )

        schema = vol.Schema(
            {
                vol.Required(CONF_HOST): str,
                vol.Required(CONF_USERNAME): str,
                vol.Required(CONF_AUTH_PROTOCOL, default="MD5"): vol.In(AUTH_PROTOCOLS),
                vol.Required(CONF_AUTH_PASSWORD): str,
                vol.Required(CONF_PRIV_PROTOCOL, default="DES"): vol.In(PRIV_PROTOCOLS),
                vol.Required(CONF_PRIV_PASSWORD): str,
                vol.Required(
                    CONF_SCAN_INTERVAL, default=DEFAULT_SCAN_INTERVAL
                ): vol.In(SCAN_INTERVAL_OPTIONS),
            }
        )
        return self.async_show_form(step_id="v3", data_schema=schema, errors=errors)
