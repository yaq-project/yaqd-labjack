__all__ = ["LabjackSensor"]

import asyncio
from typing import Dict, Any, List
from dataclasses import dataclass
import struct

from pymodbus.client.sync import ModbusTcpClient  # type: ignore
from yaqd_core import HasMeasureTrigger, IsSensor, IsDaemon

from ._bytes import *


@dataclass
class Channel:
    name: str
    modbus_address: int
    range: float
    enabled: bool


class LabjackSensor(HasMeasureTrigger, IsSensor, IsDaemon):
    _kind = "labjack-sensor"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._channels = []
        for k, d in self._config["channels"].items():
            channel = Channel(**d, name=k)
            self._channels.append(channel)
        self._channel_names = [c.name for c in self._channels if c.enabled]
        self._channel_units = {k: "V" for k in self._channel_names}
        if self._config["read_device_temperature"]:
            self._channel_names.append("device_temperature")
            self._channel_units["device_temperature"] = "K"
        # hardware configuration
        self._client = ModbusTcpClient(self._config["address"])
        self._client.connect()
        self._client.read_holding_registers(0, 2)
        for c in self._channels:
            self._client.write_registers(40_000 + c.modbus_address, float32_to_data(c.range))
        # id
        self.make = "LabJack"
        response = self._client.read_holding_registers(address=60000, count=2)
        self.model = str(data_to_float32(response.registers))
        response = self._client.read_holding_registers(address=60028, count=2)
        self.serial = str(data_to_int32(response.registers))

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
