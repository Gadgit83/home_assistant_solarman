"""The Solarman Collector integration."""

import logging

from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME

from .const import *
from .solarman import Inverter

_LOGGER = logging.getLogger(__name__)

PLATFORMS: list[str] = ["sensor","number"]

async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    
    # Store an instance of the "connecting" class that does the work of speaking
    # with your actual devices.
    # This is now in __init__.py so that it can be shared between the sensors and the configurables
    
    inverter_host = entry.data[CONF_INVERTER_HOST]
    if inverter_host == "0.0.0.0":
        inverter_host = _inverter_scanner.get_ipaddress()
        
   
    inverter_port = entry.data[CONF_INVERTER_PORT]
    inverter_sn = entry.data[CONF_INVERTER_SERIAL]
    if inverter_sn == 0:
        inverter_sn = _inverter_scanner.get_serialno()
    
    inverter_mb_slaveid = entry.data[CONF_INVERTER_MB_SLAVEID]
    if not inverter_mb_slaveid:
        inverter_mb_slaveid = DEFAULT_INVERTER_MB_SLAVEID
    lookup_file = entry.data[CONF_LOOKUP_FILE]
    path = hass.config.path('custom_components/solarman/inverter_definitions/')

    # Check input configuration.
    if inverter_host is None:
        raise vol.Invalid('configuration parameter [inverter_host] does not have a value')
    if inverter_sn is None:
        raise vol.Invalid('configuration parameter [inverter_serial] does not have a value')
    
    hass.data.setdefault(DOMAIN, {})["inverter"] = Inverter(path, inverter_sn, inverter_host, inverter_port, inverter_mb_slaveid, lookup_file)
    
    """Set up Solarman Collector from a config entry."""
    _LOGGER.debug(f'__init__.py:async_setup_entry({entry.as_dict()})')
    hass.config_entries.async_setup_platforms(entry, PLATFORMS)
    entry.async_on_unload(entry.add_update_listener(update_listener))
    return True


async def async_unload_entry(hass: HomeAssistant, entry: ConfigEntry) -> bool:
    """Unload a config entry."""
    _LOGGER.debug(f'__init__.py:async_unload_entry({entry.as_dict()})')
    unload_ok = await hass.config_entries.async_unload_platforms(entry, PLATFORMS)
    if unload_ok:
        _LOGGER.debug(DOMAIN)
        _LOGGER.debug(hass.data)
        _LOGGER.debug('purge')
        
        _LOGGER.debug(hass.data[DOMAIN].pop(entry.entry_id))
    return unload_ok


async def update_listener(hass: HomeAssistant, entry: ConfigEntry) -> None:
    """Handle options update."""
    _LOGGER.debug(f'__init__.py:update_listener({entry.as_dict()})')
    hass.data[DOMAIN][entry.entry_id].config(entry)
    entry.title = entry.options[CONF_NAME]
