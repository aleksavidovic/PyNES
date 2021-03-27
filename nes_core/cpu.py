from numpy import uint8, uint16
from .exceptions import NoBusConnectedError
from bitstring import BitArray
from .bus import Bus


class CPU:
    def __init__(self):
        # TODO proper registers
        self.registers = []
        self.acc_reg = uint8(0x00)  # Accumulator register
        self.x_reg = uint8(0x00)    # X register
        self.y_reg = uint8(0x00)    # Y register
        self.stkp = uint8(0x00)     # Stack Pointer
        self.pc = uint16(0x0000)    # Program Counter
        self.status = uint8(0x00)   # Status Register
        self.bus = None
        self.operation = BitArray()

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
