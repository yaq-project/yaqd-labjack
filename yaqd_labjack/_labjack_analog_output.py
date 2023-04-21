__all__ = ["LabjackAnalogOutput"]

import asyncio
from typing import Dict, Any, List

from pymodbus.client import ModbusTcpClient  # type: ignore
from yaqd_core import IsDiscrete, HasPosition, IsDaemon

from ._bytes import *
from ._io import clients


class LabjackAnalogOutput(IsDiscrete, HasPosition, IsDaemon):
    _kind = "labjack-analog-output"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        #
        if self._config["address"] in clients:
            self._client = clients[self._config["address"]]
        else:
            self._client = ModbusTcpClient(config["address"])
            clients[self._config["address"]] = self._client

    def _set_position(self, value: float) -> None:
        self._client.write_registers(self._config["modbus_address"], float32_to_data(value))

    async def update_state(self):
        while True:
            if self._busy:
                await asyncio.sleep(0.1)
                value = self._state["destination"]
                self._state["position"] = value
                self._busy = False
            try:
                await asyncio.wait_for(self._busy_sig.wait(), timeout=1)
            except asyncio.TimeoutError:
                self._set_position(self._state["destination"])
