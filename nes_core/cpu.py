from numpy import uint8, uint16
from .exceptions import NoBusConnectedError
from bitstring import BitArray
from .bus import Bus
"""
status register enum:
C = (1 << 0) # Carry bit
Z = (1 << 1) # Carry bit
I = (1 << 2) # Carry bit
D = (1 << 3) # Carry bit
B = (1 << 4) # Carry bit
U = (1 << 5) # Carry bit
V = (1 << 6) # Carry bit
N = (1 << 7) # Carry bit
"""


class CPU:
    def __init__(self):
        self.opcode = uint8(0x00)       # Currently processed opcode
        self.cycles = 0                 # Cycles left for current opcode
        self.addr_abs = uint16(0x0000)  # Addr where instruction was called
        self.addr_rel = uint8(0x00)     # Relative addr for jumps
        self.acc_reg = uint8(0x00)      # Accumulator register
        self.x_reg = uint8(0x00)        # X register
        self.y_reg = uint8(0x00)        # Y register
        self.stkp = uint8(0x00)         # Stack Pointer
        self.pc = uint16(0x0000)        # Program Counter
        self.status_reg = uint8(0x00)   # Status Register
        self.bus = None
        self.status_map = {
                            'C': 1 << 0,  # Carry bit
                            'Z': 1 << 1,  # Zero
                            'I': 1 << 2,  # Disable Interrupts
                            'D': 1 << 3,  # Decimal Mode (Unsupported)
                            'B': 1 << 4,  # Break
                            'U': 1 << 5,  # Unused
                            'V': 1 << 6,  # Overflow
                            'N': 1 << 7   # Negative
                    }

        # 12 Addressing modes
        # IMP IMM
        # ZP0 ZPX
        # ZPY REL
        # ABS ABX
        # ABY IND
        # IZX IZY

        # 56 Opcodes
        # LDA
        # LDX
        # LDY
        # STA
        # STX

        # STY
        # TXA
        # TYA
        # TXS
        # TAY
        # TAX
        # TSX

        # PHP
        # PLP
        # PHA
        # PLA

        # ADC
        # SBC
        # CMP
        # CPX
        # CPY

        # AND
        # EOR
        # ORA
        # BIT

        # ASL
        # LSR
        # ROL
        # ROR

        # INC
        # INX
        # INY
        # DEC
        # DEX
        # DEY

        # CLC
        # CLI
        # CLV
        # CLD
        # SEC
        # SEI
        # SED

        # NOP
        # BRK

        # JMP
        # JSR
        # RTS
        # RTI

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
        pass

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