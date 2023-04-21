__all__ = ["LabjackSensor"]

import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
import struct

from pymodbus.client import ModbusTcpClient  # type: ignore
from yaqd_core import HasMeasureTrigger, IsSensor, IsDaemon

from ._bytes import *
from ._io import clients


@dataclass
class Channel:
    name: str
    modbus_address: int
    modbus_type: str
    units: str
    enabled: bool


@dataclass
class Setting:
    modbus_address: int
    modbus_type: str
    value: Any
    comment: str
    enabled: bool


class LabjackSensor(HasMeasureTrigger, IsSensor, IsDaemon):
    _kind = "labjack-sensor"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        print(self._config["channels"])
        self._channels = []
        for k, d in self._config["channels"].items():
            print(d)
            channel = Channel(**d, name=k)
            self._channels.append(channel)
        self._settings = []
        for d in self._config["settings"]:
            setting = Setting(**d)
            self._settings.append(setting)
        self._channel_names = [c.name for c in self._channels if c.enabled]
        self._channel_units = {
            k: self._config["channels"][k]["units"] for k in self._channel_names
        }
        if self._config["read_device_temperature"]:
            self._channel_names.append("device_temperature")
            self._channel_units["device_temperature"] = "K"
        # hardware configuration
        if self._config["address"] in clients:
            self._client = clients[self._config["address"]]
            self._client.connect()
        else:
            self._client = ModbusTcpClient(config["address"])
            clients[self._config["address"]] = self._client
        self._client.read_holding_registers(0, 2)
        # id
        self.make = "LabJack"
        response = self._client.read_holding_registers(address=60000, count=2)
        self.model = str(data_to_float32(response.registers))
        response = self._client.read_holding_registers(address=60028, count=2)
        self.serial = str(data_to_int32(response.registers))
        # launch settings setter
        self._loop.create_task(self._set_settings())

    async def _measure(self):
        out = dict()
        for c in self._channels:
            response = self._client.read_holding_registers(address=c.modbus_address, count=2)
            out[c.name] = data_to_float32(response.registers)
            await asyncio.sleep(0)
        if self._config["read_device_temperature"]:
            response = self._client.read_holding_registers(address=60052, count=2)
            out["device_temperature"] = data_to_float32(response.registers)
            await asyncio.sleep(0)
        if self._looping:
            await asyncio.sleep(0.01)
        return out

    async def _set_settings(self):
        while True:
            for setting in self._settings:
                data = type_to_data(setting.modbus_type, setting.value)
                print(setting.modbus_address, data)
                self._client.write_registers(setting.modbus_address, data)
                await asyncio.sleep(1)
            await asyncio.sleep(60)
