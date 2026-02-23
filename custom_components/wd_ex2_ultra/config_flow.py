"""Config flow for WD MyCloud EX2 Ultra integration."""
from __future__ import annotations

import logging
from typing import Any

import voluptuous as vol

from homeassistant import config_entries
from homeassistant.core import HomeAssistant
from homeassistant.data_entry_flow import FlowResult
from homeassistant.exceptions import HomeAssistantError

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

_LOGGER = logging.getLogger(__name__)


async def validate_snmp_connection(hass: HomeAssistant, data: dict) -> None:
    """Validate SNMP connectivity by querying the system uptime OID."""
    await hass.async_add_executor_job(_test_snmp, data)


def _test_snmp(data: dict) -> None:
    """Perform a synchronous SNMP test query."""
    from pysnmp.hlapi import (
        getCmd,
        SnmpEngine,
        CommunityData,
        UsmUserData,
        UdpTransportTarget,
        ContextData,
        ObjectType,
        ObjectIdentity,
        usmHMACMD5AuthProtocol,
        usmHMACSHAAuthProtocol,
        usmDESPrivProtocol,
        usmAesCfb128Protocol,
    )

    snmp_version = data.get(CONF_SNMP_VERSION, SNMP_VERSION_V2C)
    host = data[CONF_HOST]

    if snmp_version == SNMP_VERSION_V2C:
        auth_data = CommunityData(data.get(CONF_COMMUNITY, "public"), mpModel=1)
    else:
        auth_protocol_map = {
            "MD5": usmHMACMD5AuthProtocol,
            "SHA": usmHMACSHAAuthProtocol,
        }
        priv_protocol_map = {
            "DES": usmDESPrivProtocol,
            "AES": usmAesCfb128Protocol,
        }
        auth_data = UsmUserData(
            data[CONF_USERNAME],
            authKey=data[CONF_AUTH_PASSWORD],
            privKey=data[CONF_PRIV_PASSWORD],
            authProtocol=auth_protocol_map.get(data[CONF_AUTH_PROTOCOL], usmHMACMD5AuthProtocol),
            privProtocol=priv_protocol_map.get(data[CONF_PRIV_PROTOCOL], usmDESPrivProtocol),
        )

    transport = UdpTransportTarget((host, 161), timeout=5, retries=1)
    error_indication, error_status, error_index, _ = next(
        getCmd(
            SnmpEngine(),
            auth_data,
            transport,
            ContextData(),
            ObjectType(ObjectIdentity("1.3.6.1.2.1.1.3.0")),
        )
    )
    if error_indication:
        raise CannotConnect(str(error_indication))
    if error_status:
        raise InvalidAuth(str(error_status))


class CannotConnect(HomeAssistantError):
    """Error to indicate we cannot connect."""


class InvalidAuth(HomeAssistantError):
    """Error to indicate invalid authentication."""


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
            data = {
                CONF_SNMP_VERSION: SNMP_VERSION_V2C,
                CONF_HOST: user_input[CONF_HOST],
                CONF_COMMUNITY: user_input.get(CONF_COMMUNITY, "public"),
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            }
            try:
                await validate_snmp_connection(self.hass, data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during SNMP v2c validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"WD EX2 Ultra ({data[CONF_HOST]})",
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
        return self.async_show_form(
            step_id="v2c", data_schema=schema, errors=errors
        )

    async def async_step_v3(
        self, user_input: dict[str, Any] | None = None
    ) -> FlowResult:
        """Step 2b: SNMPv3 credentials."""
        errors: dict[str, str] = {}

        if user_input is not None:
            data = {
                CONF_SNMP_VERSION: SNMP_VERSION_V3,
                CONF_HOST: user_input[CONF_HOST],
                CONF_USERNAME: user_input[CONF_USERNAME],
                CONF_AUTH_PROTOCOL: user_input[CONF_AUTH_PROTOCOL],
                CONF_AUTH_PASSWORD: user_input[CONF_AUTH_PASSWORD],
                CONF_PRIV_PROTOCOL: user_input[CONF_PRIV_PROTOCOL],
                CONF_PRIV_PASSWORD: user_input[CONF_PRIV_PASSWORD],
                CONF_SCAN_INTERVAL: user_input.get(CONF_SCAN_INTERVAL, DEFAULT_SCAN_INTERVAL),
            }
            try:
                await validate_snmp_connection(self.hass, data)
            except CannotConnect:
                errors["base"] = "cannot_connect"
            except InvalidAuth:
                errors["base"] = "invalid_auth"
            except Exception:  # noqa: BLE001
                _LOGGER.exception("Unexpected error during SNMP v3 validation")
                errors["base"] = "unknown"
            else:
                return self.async_create_entry(
                    title=f"WD EX2 Ultra ({data[CONF_HOST]})",
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
        return self.async_show_form(
            step_id="v3", data_schema=schema, errors=errors
        )
