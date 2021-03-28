from numpy import uint8, uint16
import logging
from .exceptions import NoBusConnectedError
from .bus import Bus

logging.basicConfig(level=logging.DEBUG)


class CPU:
    def __init__(self):
        self.opcode = uint8(0x00)  # Currently processed opcode
        self.cycles = 0  # Cycles left for current opcode
        self.addr_abs = uint16(0x0000)  # Addr where instruction was called
        self.addr_rel = uint8(0x00)  # Relative addr for jumps
        self.acc_reg = uint8(0x00)  # Accumulator register
        self.x_reg = uint8(0x00)  # X register
        self.y_reg = uint8(0x00)  # Y register
        self.stkp = uint8(0x00)  # Stack Pointer
        self.pc = uint16(0x0000)  # Program Counter
        self.status_reg = uint8(0x00)  # Status Register
        self.bus = None
        self.status_map = {
            'C': 1 << 0,  # Carry bit
            'Z': 1 << 1,  # Zero
            'I': 1 << 2,  # Disable Interrupts
            'D': 1 << 3,  # Decimal Mode (Unsupported)
            'B': 1 << 4,  # Break
            'U': 1 << 5,  # Unused
            'V': 1 << 6,  # Overflow
            'N': 1 << 7  # Negative
        }

        self.instructions_lookup = [
            {
                # 0x00
                'name': 'BRK',
                'operation': self.BRK,
                'addr_mode': self.IMM,
                'cycles': 7
            },
            {
                # 0x01
                'name': 'ORA',
                'operation': self.ORA,
                'addr_mode': self.IZX,
                'cycles': 6
            }
        ]

    # 12 Addressing modes
    # Each addressing mode function returns an int indicating
    # the number of additional clock cycles required for it
    # IMP IMM
    # ZP0 ZPX
    # ZPY REL
    # ABS ABX
    # ABY IND
    # IZX IZY

    def IMM(self):
        logging.debug("IMM addressing mode activated")
        return 0

    def IZX(self):
        logging.debug("IZX addressing mode activated")
        return 0

    # TODO: 56 Opcodes
    # OPERATIONS
    def BRK(self):
        return 0

    def ORA(self):
        return 0

    # I/O methods
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

    def clock(self):
        if self.cycles == 0:
            self.opcode = self.read_from_bus(self.pc)
            self.pc += 1
            instruction = self.instructions_lookup[self.opcode]

            # Get starting number of cycles
            self.cycles = instruction['cycles']

            # Address mode and operation can require additional cycles
            additional_cycles_addr_mode = instruction['addr_mode']()
            additional_cycles_operation = instruction['operation']()
            self.cycles += additional_cycles_addr_mode + additional_cycles_operation

        self.cycles -= 1

    def illegal_opcode(self):
        pass

    def reset(self):
        pass

    def irq(self):  # Interrupt request signal
        pass

    def nmi(self):  # Non maskable interrupt
        pass

    def fetch(self):
        pass
