from __future__ import annotations
from numpy import uint16, uint8
from typing import TYPE_CHECKING
if TYPE_CHECKING:
    from cpu import CPU


class Bus:
    def __init__(self):
        self.ram = [uint8(0)] * (64 * 1024)

    def write(self, address: uint16, data: uint8):
        if 0x0000 > address or address > 0xFFFF:
            raise ValueError(f"{address} address out of range")

        if isinstance(data, uint8):
            self.ram[address] = data
        else:
            raise TypeError("uint8 must be passed to the bus")

    def read(self, address: uint16, b_read_only=False):
        pass
