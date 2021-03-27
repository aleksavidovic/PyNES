from numpy import uint8, uint16
from typing import TYPE_CHECKING
from .exceptions import NoBusConnectedError
from .bus import Bus


class CPU:
    def __init__(self):
        # TODO proper registers
        self.registers = []
        self.bus = None

    def process_instruction(self, instruction: bytes):
        # TODO process instruction
        print(instruction)

    def connect_bus(self, bus: Bus):
        self.bus = bus

    def write_to_bus(self, address: uint16, data: uint8):
        if self.bus is not None:
            self.bus.write(address, data)
        else:
            raise NoBusConnectedError

    def read_from_bus(self, address: uint16):
        if self.bus is not None:
            return self.bus.read(address, False)
        else:
            raise NoBusConnectedError
