from numpy import uint8, uint16
from collections import namedtuple
import logging
from .exceptions import NoBusConnectedError
from .bus import Bus

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(message)s')

ins = namedtuple('Instruction', ['mnemonic', 'operation', 'addr_mode', 'cycles'])

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

        # Making this a 16x16 table for readability, RIP PEP8, RIP 80 char limit
        self.instructions_lookup = (
            ins("BRK", self.BRK, self.IMM, 7), ins("ORA", self.ORA, self.IZX, 6), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("ORA", self.ORA, self.ZP0, 3), ins("ASL", self.ASL, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PHP", self.PHP, self.IMP, 3), ins("ORA", self.ORA, self.IMM, 2), ins("ASL", self.ASL, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ABS, 4), ins("ASL", self.ASL, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BPL", self.BPL, self.REL, 2), ins("ORA", self.ORA, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ZPX, 4), ins("ASL", self.ASL, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLC", self.CLC, self.IMP, 2), ins("ORA", self.ORA, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ABX, 4), ins("ASL", self.ASL, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
            ins("JSR", self.JSR, self.ABS, 6), ins("AND", self.AND, self.IZX, 6), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("BIT", self.BIT, self.ZP0, 3), ins("AND", self.AND, self.ZP0, 3), ins("ROL", self.ROL, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PLP", self.PLP, self.IMP, 4), ins("AND", self.AND, self.IMM, 2), ins("ROL", self.ROL, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("BIT", self.BIT, self.ABS, 4), ins("AND", self.AND, self.ABS, 4), ins("ROL", self.ROL, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BMI", self.BMI, self.REL, 2), ins("AND", self.AND, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("AND", self.AND, self.ZPX, 4), ins("ROL", self.ROL, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SEC", self.SEC, self.IMP, 2), ins("AND", self.AND, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("AND", self.AND, self.ABX, 4), ins("ROL", self.ROL, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
            ins("RTI", self.RTI, self.IMP, 6), ins("EOR", self.EOR, self.IZX, 6), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("EOR", self.EOR, self.ZP0, 3), ins("LSR", self.LSR, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PHA", self.PHA, self.IMP, 3), ins("EOR", self.EOR, self.IMM, 2), ins("LSR", self.LSR, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("JMP", self.JMP, self.ABS, 3), ins("EOR", self.EOR, self.ABS, 4), ins("LSR", self.LSR, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BVC", self.BVC, self.REL, 2), ins("EOR", self.EOR, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("EOR", self.EOR, self.ZPX, 4), ins("LSR", self.LSR, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLI", self.CLI, self.IMP, 2), ins("EOR", self.EOR, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("EOR", self.EOR, self.ABX, 4), ins("LSR", self.LSR, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
            ins("RTS", self.RTS, self.IMP, 6), ins("ADC", self.ADC, self.IZX, 6), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("ADC", self.ADC, self.ZP0, 3), ins("ROR", self.ROR, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PLA", self.PLA, self.IMP, 4), ins("ADC", self.ADC, self.IMM, 2), ins("ROR", self.ROR, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("JMP", self.JMP, self.IND, 5), ins("ADC", self.ADC, self.ABS, 4), ins("ROR", self.ROR, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BVS", self.BVS, self.REL, 2), ins("ADC", self.ADC, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("ADC", self.ADC, self.ZPX, 4), ins("ROR", self.ROR, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SEI", self.SEI, self.IMP, 2), ins("ADC", self.ADC, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("ADC", self.ADC, self.ABX, 4), ins("ROR", self.ROR, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 2), ins("STA", self.STA, self.IZX, 6), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 6), ins("STY", self.STY, self.ZP0, 3), ins("STA", self.STA, self.ZP0, 3), ins("STX", self.STX, self.ZP0, 3), ins("???", self.XXX, self.IMP, 3), ins("DEY", self.DEY, self.IMP, 2), ins("???", self.NOP, self.IMP, 2), ins("TXA", self.TXA, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("STY", self.STY, self.ABS, 4), ins("STA", self.STA, self.ABS, 4), ins("STX", self.STX, self.ABS, 4), ins("???", self.XXX, self.IMP, 4),
            ins("BCC", self.BCC, self.REL, 2), ins("STA", self.STA, self.IZY, 6), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 6), ins("STY", self.STY, self.ZPX, 4), ins("STA", self.STA, self.ZPX, 4), ins("STX", self.STX, self.ZPY, 4), ins("???", self.XXX, self.IMP, 4), ins("TYA", self.TYA, self.IMP, 2), ins("STA", self.STA, self.ABY, 5), ins("TXS", self.TXS, self.IMP, 2), ins("???", self.XXX, self.IMP, 5), ins("???", self.NOP, self.IMP, 5), ins("STA", self.STA, self.ABX, 5), ins("???", self.XXX, self.IMP, 5), ins("???", self.XXX, self.IMP, 5),
            ins("LDY", self.LDY, self.IMM, 2), ins("LDA", self.LDA, self.IZX, 6), ins("LDX", self.LDX, self.IMM, 2), ins("???", self.XXX, self.IMP, 6), ins("LDY", self.LDY, self.ZP0, 3), ins("LDA", self.LDA, self.ZP0, 3), ins("LDX", self.LDX, self.ZP0, 3), ins("???", self.XXX, self.IMP, 3), ins("TAY", self.TAY, self.IMP, 2), ins("LDA", self.LDA, self.IMM, 2), ins("TAX", self.TAX, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("LDY", self.LDY, self.ABS, 4), ins("LDA", self.LDA, self.ABS, 4), ins("LDX", self.LDX, self.ABS, 4), ins("???", self.XXX, self.IMP, 4),
            ins("BCS", self.BCS, self.REL, 2), ins("LDA", self.LDA, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 5), ins("LDY", self.LDY, self.ZPX, 4), ins("LDA", self.LDA, self.ZPX, 4), ins("LDX", self.LDX, self.ZPY, 4), ins("???", self.XXX, self.IMP, 4), ins("CLV", self.CLV, self.IMP, 2), ins("LDA", self.LDA, self.ABY, 4), ins("TSX", self.TSX, self.IMP, 2), ins("???", self.XXX, self.IMP, 4), ins("LDY", self.LDY, self.ABX, 4), ins("LDA", self.LDA, self.ABX, 4), ins("LDX", self.LDX, self.ABY, 4), ins("???", self.XXX, self.IMP, 4),
            ins("CPY", self.CPY, self.IMM, 2), ins("CMP", self.CMP, self.IZX, 6), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("CPY", self.CPY, self.ZP0, 3), ins("CMP", self.CMP, self.ZP0, 3), ins("DEC", self.DEC, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("INY", self.INY, self.IMP, 2), ins("CMP", self.CMP, self.IMM, 2), ins("DEX", self.DEX, self.IMP, 2), ins("???", self.XXX, self.IMP, 2), ins("CPY", self.CPY, self.ABS, 4), ins("CMP", self.CMP, self.ABS, 4), ins("DEC", self.DEC, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BNE", self.BNE, self.REL, 2), ins("CMP", self.CMP, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("CMP", self.CMP, self.ZPX, 4), ins("DEC", self.DEC, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLD", self.CLD, self.IMP, 2), ins("CMP", self.CMP, self.ABY, 4), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("CMP", self.CMP, self.ABX, 4), ins("DEC", self.DEC, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
            ins("CPX", self.CPX, self.IMM, 2), ins("SBC", self.SBC, self.IZX, 6), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("CPX", self.CPX, self.ZP0, 3), ins("SBC", self.SBC, self.ZP0, 3), ins("INC", self.INC, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("INX", self.INX, self.IMP, 2), ins("SBC", self.SBC, self.IMM, 2), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.SBC, self.IMP, 2), ins("CPX", self.CPX, self.ABS, 4), ins("SBC", self.SBC, self.ABS, 4), ins("INC", self.INC, self.ABS, 6), ins("???", self.XXX, self.IMP, 6),
            ins("BEQ", self.BEQ, self.REL, 2), ins("SBC", self.SBC, self.IZY, 5), ins("???", self.XXX, self.IMP, 2), ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("SBC", self.SBC, self.ZPX, 4), ins("INC", self.INC, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SED", self.SED, self.IMP, 2), ins("SBC", self.SBC, self.ABY, 4), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7), ins("???", self.NOP, self.IMP, 4), ins("SBC", self.SBC, self.ABX, 4), ins("INC", self.INC, self.ABX, 7), ins("???", self.XXX, self.IMP, 7),
        )
        """
        {
            # 0x00
            'mnemonic': 'BRK',
            'operation': self.BRK,
            'addr_mode': self.IMM,
            'cycles': 7
        },
        {
            # 0x01
            'mnemonic': 'ORA',
            'operation': self.ORA,
            'addr_mode': self.IZX,
            'cycles': 6
        },
        {
            # 0x02
            'mnemonic': '???',
            'operation': self.XXX,
        }
        """

    # 12 Addressing modes
    # Each addressing mode function returns an int indicating
    # the number of additional clock cycles required for it
    def IMP(self):
        logging.debug("IMP addressing mode activated")
        return 0

    def IMM(self):
        logging.debug("IMM addressing mode activated")
        return 0

    def ZP0(self):
        logging.debug("ZP0 addressing mode activated")
        return 0

    def ZPX(self):
        logging.debug("ZPX addressing mode activated")
        return 0

    def ZPY(self):
        logging.debug("ZPY addressing mode activated")
        return 0

    def REL(self):
        logging.debug("REL addressing mode activated")
        return 0

    def ABS(self):
        logging.debug("ABS addressing mode activated")
        return 0

    def ABX(self):
        logging.debug("ABX addressing mode activated")
        return 0

    def ABY(self):
        logging.debug("ABY addressing mode activated")
        return 0

    def IND(self):
        logging.debug("IND addressing mode activated")
        return 0

    def IZX(self):
        logging.debug("IZX addressing mode activated")
        return 0

    def IZY(self):
        logging.debug("IZY addressing mode activated")
        return 0

    # TODO: 56 Opcodes
    # OPERATIONS
    def XXX(self):
        #  illegal opcode handler
        return 0

    def NOP(self):
        # Non-official opcode handler
        return 1

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
            logging.debug(f'Executing instruction {instruction.mnemonic}')

            # Get starting number of cycles
            self.cycles = instruction.cycles

            # Address mode and operation can require additional cycles
            additional_cycles_addr_mode = instruction.addr_mode()
            additional_cycles_operation = instruction.operation()
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
