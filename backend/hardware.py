"""Hardware abstraction. Simulator works now; MCP23017 implementation comes after wiring."""
from __future__ import annotations

from dataclasses import dataclass, field


@dataclass
class HardwareController:
    mode: str = "simulator"
    lights: list[str] = field(default_factory=lambda: ["off"] * 10)

    async def set_light(self, button: int, color: str) -> None:
        if 0 <= button < 10:
            self.lights[button] = color
        # Physical mode will write to the MCP23017 here.

    async def all_off(self) -> None:
        self.lights = ["off"] * 10

