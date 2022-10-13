__all__ = ["LabjackDigitalOutput"]

import asyncio
from typing import Dict, Any, List

from pymodbus.client.TCP import ModbusTcpClient  # type: ignore
from yaqd_core import IsDiscrete, HasPosition, IsDaemon


class LabjackDigitalOutput(IsDiscrete, HasPosition, IsDaemon):
    _kind = "labjack-digital-output"

    def __init__(self, name, config, config_filepath):
        super().__init__(name, config, config_filepath)
        self._position_identifiers = {"low": 0, "high": 1}

    def _set_position(self, value):
        raise NotImplementedError

    async def update_state(self):
        while True:
            self._position = self._controller.value
            if self._position:
                self._state["position_identifier"] = "high"
            else:
                self._state["position_identifier"] = "low"
            self._busy = False
            await self._busy_sig.wait()
