__all__ = ["LabjackDigitalOutput"]

import asyncio
from typing import Dict, Any, List

from pymodbus.client import ModbusTcpClient  # type: ignore
from yaqd_core import IsDiscrete, HasPosition, IsDaemon

from ._bytes import *


class LabjackDigitalOutput(IsDiscrete, HasPosition, IsDaemon):
    _kind = "labjack-digital-output"

    clients: Dict[str, ModbusTcpClient] = {}

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        if self._position_identifiers:  # was set in config
            self._position_identifiers = config["identifiers"]
        else:
            if config["pin_type"] == "FIO":
                self._position_identifiers = {"low": 0.0, "high": 1.0}
            elif config["pin_type"] == "DAC":
                self._position_identifiers = {"low": 0.0, "high": 5.0}
            if config["invert"]:
                self._position_identifiers["low"] = self._position_identifiers["high"]
                self._position_identifiers["high"] = 0.0
        #
        if self._config["address"] in LabjackDigitalOutput.clients:
            self._client = LabjackDigitalOutput.clients[self._config["address"]]
        else:
            self._client = ModbusTcpClient(config["address"])
            LabjackDigitalOutput.clients[self._config["address"]] = self._client

    def _set_position(self, value: float) -> None:
        if self._config["pin_type"] == "FIO":
            value = int(value)
            self._client.write_register(self._config["modbus_address"], uint16_to_data(value))
        elif self._config["pin_type"] == "DAC":
            value = float(value)
            self._client.write_registers(self._config["modbus_address"], float32_to_data(value))

    async def _set_position_later(self, value):
        while True:
            await self._busy_sig.wait()

    async def update_state(self):
        while True:
            if self._busy:
                await asyncio.sleep(0.1)
                value = self._state["destination"]
                self._state["position"] = value
                # identifiers might be many-valued, because users are allowed to put whatever in config
                identifier = ""
                min_diff_seen = float("inf")
                for k, v in self._position_identifiers.items():
                    diff = abs(value - v)
                    if diff < min_diff_seen:
                        min_diff_seen = diff
                        identifier = k
                self._state["position_identifier"] = identifier
                self._busy = False
            try:
                await asyncio.wait_for(self._busy_sig.wait(), timeout=1)
            except asyncio.TimeoutError:
                self._set_position(self._state["destination"])
