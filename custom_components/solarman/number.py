
################################################################################
#   Solarman local interface.
#
#   This component can retrieve data from the solarman dongle using version 5
#   of the protocol.
#
###############################################################################

import logging
import voluptuous as vol
from homeassistant.core import HomeAssistant
from homeassistant.config_entries import ConfigEntry
from homeassistant.const import CONF_NAME
from homeassistant.components.number import NumberEntity
from homeassistant.helpers.entity_platform import AddEntitiesCallback

from .const import *
from .solarman import Inverter
from .scanner import InverterScanner

_LOGGER = logging.getLogger(__name__)
_inverter_scanner = InverterScanner()

def _do_setup_platform(hass: HomeAssistant, config, async_add_entities : AddEntitiesCallback):

    inverter_name = config.get(CONF_NAME)

    # Get the shared inverter class
    inverter = hass.data[DOMAIN]["inverter"]
    #  Prepare the sensor entities.
    hass_sensors = []
    
    #  Prepare the control entities.
    for sensor in inverter.get_configurables():
        hass_sensors.append(SolarmanConfigurable(inverter_name, inverter, sensor, inverter._serial))
        _LOGGER.debug(sensor)

    _LOGGER.debug(f'sensor.py:_do_setup_platform: async_add_entities')
    _LOGGER.debug(hass_sensors)

    async_add_entities(hass_sensors)
    
# Set-up from configuration.yaml
async def async_setup_platform(hass: HomeAssistant, config, async_add_entities : AddEntitiesCallback, discovery_info=None):
    _LOGGER.debug(f'number.py:async_setup_platform: {config}') 
    _do_setup_platform(hass, config, async_add_entities)
       
# Set-up from the entries in config-flow
async def async_setup_entry(hass: HomeAssistant, entry: ConfigEntry, async_add_entities: AddEntitiesCallback):
    _LOGGER.debug(f'number.py:async_setup_entry: {entry.options}') 
    _do_setup_platform(hass, entry.options, async_add_entities)


#############################################################################################################
#  Entity displaying a numeric field read from the inverter
#   Overrides the Text sensor and supply the device class, last_reset and unit of measurement
#############################################################################################################

class SolarmanConfigurable(NumberEntity):
    
    def __init__(self, inverter_name, inverter, sensor, sn) -> None:
        # Set up the internal parameters
        self._inverter_name = inverter_name
        self.inverter = inverter
        self._sn = sn
        self._attr_min_value = sensor['min']
        self._attr_max_value = sensor['max']
        self._attr_mode = 'box'
        self.p_state = None
        self.rule = sensor['rule']
        self._field_name = sensor['name']
        self._registers = sensor['registers']
        self.uom = sensor['uom']
        
        if 'lookup' in sensor:
            self._lookup_values = sensor['lookup']
        else:
            self._lookup_values = []
        
        if 'data_type' in sensor:
            self._data_type = sensor['data_type']
        else:
            self._data_type = '';
        if 'icon' in sensor:
            self.p_icon = sensor['icon']
        else:
            self.p_icon = ''
        return
        

    @property
    def name(self):
        #  Return the name of the sensor.
        return "{} {}".format(self._inverter_name, self._field_name)

    @property
    def unique_id(self):
        # Return a unique_id based on the serial number
        return "{}_{}_{}".format(self._inverter_name, self._sn, self._field_name)

    @property
    def icon(self):
        #  Return the icon of the sensor. """
        return self.p_icon
        
    @property
    def unit_of_measurement(self):
        return self.uom
        
    @property
    def value(self) -> float:
        return self.p_state
        
    def set_value(self, value: float) -> None:
    #async def async_set_value(self, value: float) -> None:
        """Update the current value."""
        _LOGGER.debug('set configurable value')
        #self.p_state = value
        perform_update = True
        
        if self.rule == 7:
            _LOGGER.debug(f'time update!:{value}')
        
        # Check values are in range
        if value <= self._attr_max_value and value >= self._attr_min_value:
        
            # If we have pre-determined values, then check the set value is one of those
            _LOGGER.debug(f'lookup_values:{self._lookup_values}')
            if self._lookup_values != []:
                value = int(value)
                _LOGGER.debug(f'value:{value}')
                if self.lookup_valid(value, self._lookup_values):
                    _LOGGER.debug(f'Found value:{value} in definition with lookup_valid:{self._lookup_values}')
                else:
                    perform_update = False
                    
            _LOGGER.debug(f'data type:{self._data_type}')
            if self._data_type == 'U16':
                value = int(value)
            
            value = int(value)
        else:
            perform_update = False
            
        if perform_update == True:
            _LOGGER.debug(f'Update Register:{self._registers} with value:{value}')
            self.inverter.update_configurable(self._registers,value)
        else:
            raise ValueError(f'Configurable parameter {self._field_name} out of range')
        
    def update(self):
        #  Update this sensor using the data.
        #  Get the latest data and use it to update our sensor state.
        #  Retrieve the sensor data from actual interface
        self.inverter.update()
        #_LOGGER.debug('update configurable!')
        #_LOGGER.debug(self._field_name)

        val = self.inverter.get_current_val()
        #_LOGGER.debug(val)
        if val is not None:
            if self._field_name in val:
                self.p_state = val[self._field_name]
                
    def lookup_value (self, value, options):
        for o in options:
            if (o['key'] == value):
                return o['value']
        return "LOOKUP"
    
    def lookup_valid (self, value, options):
        for o in options:
            if (o['key'] == value):
                return True
        return False