"""Tests for the Eva Calor config flow."""
from unittest.mock import patch

from pyevacalor import (  # pylint: disable=redefined-builtin
    ConnectionError,
    Error as EvaCalorError,
    UnauthorizedError,
)

from homeassistant import config_entries, data_entry_flow
from homeassistant.components.evacalor.const import CONF_UUID, DOMAIN
from homeassistant.const import (
    CONF_EMAIL,
    CONF_PASSWORD,
)

from tests.common import mock_coro


async def test_full_form_flow(hass):
    """Test we get the form."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )
    assert result["type"] == "form"
    assert result["errors"] == {}

    with patch("homeassistant.components.evacalor.config_flow.evacalor"), patch(
        "homeassistant.components.evacalor.async_setup", return_value=mock_coro(True)
    ) as mock_setup, patch(
        "homeassistant.components.evacalor.async_setup_entry",
        return_value=mock_coro(True),
    ) as mock_setup_entry:
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_UUID: "AABBCCDDEEFF",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_CREATE_ENTRY
    assert result2["title"] == DOMAIN
    assert result2["data"] == {
        CONF_EMAIL: "test-username",
        CONF_PASSWORD: "test-password",
        CONF_UUID: "AABBCCDDEEFF",
    }
    await hass.async_block_till_done()
    assert len(mock_setup.mock_calls) == 1
    assert len(mock_setup_entry.mock_calls) == 1


async def test_form_abort_if_device_already_configured(hass):
    """Test we abort if device is already configured."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.evacalor.config_flow.EvaCalorConfigFlow._entry_in_configuration_exists",
        return_value=mock_coro(True),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_UUID: "AABBCCDDEEFF",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_ABORT
    assert result2["reason"] == "device_already_configured"


async def test_form_invalid_auth(hass):
    """Test we handle invalid auth."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.evacalor.config_flow.evacalor",
        side_effect=UnauthorizedError("explanation"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_UUID: "AABBCCDDEEFF",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unauthorized"}


async def test_form_cannot_connect(hass):
    """Test we handle cannot connect error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.evacalor.config_flow.evacalor",
        side_effect=ConnectionError("explanation"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_UUID: "AABBCCDDEEFF",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "connection_error"}


async def test_form_unknown_error(hass):
    """Test we handle unknown error."""
    result = await hass.config_entries.flow.async_init(
        DOMAIN, context={"source": config_entries.SOURCE_USER}
    )

    with patch(
        "homeassistant.components.evacalor.config_flow.evacalor",
        side_effect=EvaCalorError("explanation"),
    ):
        result2 = await hass.config_entries.flow.async_configure(
            result["flow_id"],
            {
                CONF_EMAIL: "test-username",
                CONF_PASSWORD: "test-password",
                CONF_UUID: "AABBCCDDEEFF",
            },
        )

    assert result2["type"] == data_entry_flow.RESULT_TYPE_FORM
    assert result2["errors"] == {"base": "unknown_error"}
