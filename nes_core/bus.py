from __future__ import annotations
from numpy import uint16, uint8
from typing import TYPE_CHECKING
from .exceptions import AddressOutOfBoundsError
if TYPE_CHECKING:
    from cpu import CPU


class Bus:
    def __init__(self):
        self.ram = [uint8(0)] * (64 * 1024)
        self.first_address = uint16(0x0000)
        self.last_address = uint16(0xFFFF)

    def address_in_range(self, address: uint16):
        if self.first_address > address or address > self.last_address:
            return False
        else:
            return True

    def write(self, address: uint16, data: uint8):
        if self.address_in_range(address):
            if isinstance(data, uint8):
                self.ram[address] = data
            else:
                raise TypeError("uint8 must be passed to the bus")
        else:
            raise AddressOutOfBoundsError(address)

    def read(self, address: uint16, b_read_only=False):
        return self.ram[address]
