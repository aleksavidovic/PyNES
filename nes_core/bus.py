from __future__ import annotations
from numpy import uint16, uint8
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU


class Bus:
    def __init__(self, cpu: CPU):
        self.cpu = cpu
        self.ram = [uint8(0)] * (64 * 1024)

    def write(self, address: uint16, data: uint8):
        pass

    def read(self, address: uint16, b_read_only=False):
        pass
