from numpy import uint8, uint16
from collections import namedtuple
import logging
from .exceptions import NoBusConnectedError
from .bus import Bus

logging.basicConfig(level=logging.DEBUG, format='%(asctime)s - %(levelname)s - %(message)s')

ins = namedtuple('Instruction', ['mnemonic', 'operation', 'addr_mode', 'cycles'])


class CPU:
    def __init__(self):
        self.opcode = uint8(0x00)  # Currently processed opcode
        self.cycles = 0  # Cycles left for current opcode
        self.addr_abs = uint16(0x0000)  # Address where instruction was called
        self.addr_rel = uint8(0x00)  # Relative address for jumps
        self.fetched = uint8(0x00)  # Data fetched for operation
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
            'N': 1 << 7   # Negative
        }

        self.instructions_lookup = (
            ins("BRK", self.BRK, self.IMM, 7), ins("ORA", self.ORA, self.IZX, 6), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("ORA", self.ORA, self.ZP0, 3),
            ins("ASL", self.ASL, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PHP", self.PHP, self.IMP, 3),
            ins("ORA", self.ORA, self.IMM, 2), ins("ASL", self.ASL, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ABS, 4), ins("ASL", self.ASL, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BPL", self.BPL, self.REL, 2), ins("ORA", self.ORA, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ZPX, 4),
            ins("ASL", self.ASL, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLC", self.CLC, self.IMP, 2),
            ins("ORA", self.ORA, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("ORA", self.ORA, self.ABX, 4), ins("ASL", self.ASL, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
            ins("JSR", self.JSR, self.ABS, 6), ins("AND", self.AND, self.IZX, 6), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("BIT", self.BIT, self.ZP0, 3), ins("AND", self.AND, self.ZP0, 3),
            ins("ROL", self.ROL, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PLP", self.PLP, self.IMP, 4),
            ins("AND", self.AND, self.IMM, 2), ins("ROL", self.ROL, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("BIT", self.BIT, self.ABS, 4), ins("AND", self.AND, self.ABS, 4), ins("ROL", self.ROL, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BMI", self.BMI, self.REL, 2), ins("AND", self.AND, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("AND", self.AND, self.ZPX, 4),
            ins("ROL", self.ROL, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SEC", self.SEC, self.IMP, 2),
            ins("AND", self.AND, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("AND", self.AND, self.ABX, 4), ins("ROL", self.ROL, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
            ins("RTI", self.RTI, self.IMP, 6), ins("EOR", self.EOR, self.IZX, 6), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("EOR", self.EOR, self.ZP0, 3),
            ins("LSR", self.LSR, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PHA", self.PHA, self.IMP, 3),
            ins("EOR", self.EOR, self.IMM, 2), ins("LSR", self.LSR, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("JMP", self.JMP, self.ABS, 3), ins("EOR", self.EOR, self.ABS, 4), ins("LSR", self.LSR, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BVC", self.BVC, self.REL, 2), ins("EOR", self.EOR, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("EOR", self.EOR, self.ZPX, 4),
            ins("LSR", self.LSR, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLI", self.CLI, self.IMP, 2),
            ins("EOR", self.EOR, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("EOR", self.EOR, self.ABX, 4), ins("LSR", self.LSR, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
            ins("RTS", self.RTS, self.IMP, 6), ins("ADC", self.ADC, self.IZX, 6), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 3), ins("ADC", self.ADC, self.ZP0, 3),
            ins("ROR", self.ROR, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("PLA", self.PLA, self.IMP, 4),
            ins("ADC", self.ADC, self.IMM, 2), ins("ROR", self.ROR, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("JMP", self.JMP, self.IND, 5), ins("ADC", self.ADC, self.ABS, 4), ins("ROR", self.ROR, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BVS", self.BVS, self.REL, 2), ins("ADC", self.ADC, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("ADC", self.ADC, self.ZPX, 4),
            ins("ROR", self.ROR, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SEI", self.SEI, self.IMP, 2),
            ins("ADC", self.ADC, self.ABY, 4), ins("???", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("ADC", self.ADC, self.ABX, 4), ins("ROR", self.ROR, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 2), ins("STA", self.STA, self.IZX, 6), ins("???", self.NOP, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 6), ins("STY", self.STY, self.ZP0, 3), ins("STA", self.STA, self.ZP0, 3),
            ins("STX", self.STX, self.ZP0, 3), ins("???", self.XXX, self.IMP, 3), ins("DEY", self.DEY, self.IMP, 2),
            ins("???", self.NOP, self.IMP, 2), ins("TXA", self.TXA, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("STY", self.STY, self.ABS, 4), ins("STA", self.STA, self.ABS, 4), ins("STX", self.STX, self.ABS, 4),
            ins("???", self.XXX, self.IMP, 4),
            ins("BCC", self.BCC, self.REL, 2), ins("STA", self.STA, self.IZY, 6), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 6), ins("STY", self.STY, self.ZPX, 4), ins("STA", self.STA, self.ZPX, 4),
            ins("STX", self.STX, self.ZPY, 4), ins("???", self.XXX, self.IMP, 4), ins("TYA", self.TYA, self.IMP, 2),
            ins("STA", self.STA, self.ABY, 5), ins("TXS", self.TXS, self.IMP, 2), ins("???", self.XXX, self.IMP, 5),
            ins("???", self.NOP, self.IMP, 5), ins("STA", self.STA, self.ABX, 5), ins("???", self.XXX, self.IMP, 5),
            ins("???", self.XXX, self.IMP, 5),
            ins("LDY", self.LDY, self.IMM, 2), ins("LDA", self.LDA, self.IZX, 6), ins("LDX", self.LDX, self.IMM, 2),
            ins("???", self.XXX, self.IMP, 6), ins("LDY", self.LDY, self.ZP0, 3), ins("LDA", self.LDA, self.ZP0, 3),
            ins("LDX", self.LDX, self.ZP0, 3), ins("???", self.XXX, self.IMP, 3), ins("TAY", self.TAY, self.IMP, 2),
            ins("LDA", self.LDA, self.IMM, 2), ins("TAX", self.TAX, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("LDY", self.LDY, self.ABS, 4), ins("LDA", self.LDA, self.ABS, 4), ins("LDX", self.LDX, self.ABS, 4),
            ins("???", self.XXX, self.IMP, 4),
            ins("BCS", self.BCS, self.REL, 2), ins("LDA", self.LDA, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 5), ins("LDY", self.LDY, self.ZPX, 4), ins("LDA", self.LDA, self.ZPX, 4),
            ins("LDX", self.LDX, self.ZPY, 4), ins("???", self.XXX, self.IMP, 4), ins("CLV", self.CLV, self.IMP, 2),
            ins("LDA", self.LDA, self.ABY, 4), ins("TSX", self.TSX, self.IMP, 2), ins("???", self.XXX, self.IMP, 4),
            ins("LDY", self.LDY, self.ABX, 4), ins("LDA", self.LDA, self.ABX, 4), ins("LDX", self.LDX, self.ABY, 4),
            ins("???", self.XXX, self.IMP, 4),
            ins("CPY", self.CPY, self.IMM, 2), ins("CMP", self.CMP, self.IZX, 6), ins("???", self.NOP, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("CPY", self.CPY, self.ZP0, 3), ins("CMP", self.CMP, self.ZP0, 3),
            ins("DEC", self.DEC, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("INY", self.INY, self.IMP, 2),
            ins("CMP", self.CMP, self.IMM, 2), ins("DEX", self.DEX, self.IMP, 2), ins("???", self.XXX, self.IMP, 2),
            ins("CPY", self.CPY, self.ABS, 4), ins("CMP", self.CMP, self.ABS, 4), ins("DEC", self.DEC, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BNE", self.BNE, self.REL, 2), ins("CMP", self.CMP, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("CMP", self.CMP, self.ZPX, 4),
            ins("DEC", self.DEC, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("CLD", self.CLD, self.IMP, 2),
            ins("CMP", self.CMP, self.ABY, 4), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("CMP", self.CMP, self.ABX, 4), ins("DEC", self.DEC, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
            ins("CPX", self.CPX, self.IMM, 2), ins("SBC", self.SBC, self.IZX, 6), ins("???", self.NOP, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("CPX", self.CPX, self.ZP0, 3), ins("SBC", self.SBC, self.ZP0, 3),
            ins("INC", self.INC, self.ZP0, 5), ins("???", self.XXX, self.IMP, 5), ins("INX", self.INX, self.IMP, 2),
            ins("SBC", self.SBC, self.IMM, 2), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.SBC, self.IMP, 2),
            ins("CPX", self.CPX, self.ABS, 4), ins("SBC", self.SBC, self.ABS, 4), ins("INC", self.INC, self.ABS, 6),
            ins("???", self.XXX, self.IMP, 6),
            ins("BEQ", self.BEQ, self.REL, 2), ins("SBC", self.SBC, self.IZY, 5), ins("???", self.XXX, self.IMP, 2),
            ins("???", self.XXX, self.IMP, 8), ins("???", self.NOP, self.IMP, 4), ins("SBC", self.SBC, self.ZPX, 4),
            ins("INC", self.INC, self.ZPX, 6), ins("???", self.XXX, self.IMP, 6), ins("SED", self.SED, self.IMP, 2),
            ins("SBC", self.SBC, self.ABY, 4), ins("NOP", self.NOP, self.IMP, 2), ins("???", self.XXX, self.IMP, 7),
            ins("???", self.NOP, self.IMP, 4), ins("SBC", self.SBC, self.ABX, 4), ins("INC", self.INC, self.ABX, 7),
            ins("???", self.XXX, self.IMP, 7),
        )

    # 12 Addressing modes
    # Each addressing mode function returns an int indicating
    # the number of additional clock cycles required for it
    def IMP(self):
        """IMP - Implied Addressing Mode
        Instruction doesn't operate on data, so no data is provided
        It might use accumulator register so that is fetched just in case"""
        logging.debug("IMP addressing mode activated")
        self.fetched = self.acc_reg  # consider moving into fetch method
        return 0

    def IMM(self):
        """IMM - Immediate Mode Addressing
        Data is supplied as a part of the instruction
        """
        logging.debug("IMM addressing mode activated")
        self.pc += 1
        self.addr_abs = self.pc
        return 0

    def ZP0(self):
        """ZP0 - Zero Page Addressing"""
        logging.debug("ZP0 addressing mode activated")
        self.addr_abs = self.read_from_bus(self.pc)
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def ZPX(self):
        """ZPX - Zero Page Addressing with X Register Offset"""
        logging.debug("ZPX addressing mode activated")
        self.addr_abs = (self.read_from_bus(self.pc) + self.x_reg)
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def ZPY(self):
        """ZPY - Zero Page Addressing with Y Register Offset"""
        logging.debug("ZPY addressing mode activated")
        self.addr_abs = (self.read_from_bus(self.pc) + self.y_reg)
        self.pc += 1
        self.addr_abs &= 0x00FF
        return 0

    def REL(self):
        logging.debug("CPU.REL() - Relative addressing mode activated")
        self.addr_rel = self.read_from_bus(self.pc)
        self.pc += 1
        if self.addr_rel & 0x80:
            self.addr_rel |= 0xFF00
        return 0

    def ABS(self):
        """ABS - Absolute Addressing Mode"""
        logging.debug("ABS addressing mode activated")
        lo = self.read_from_bus(self.pc)
        self.pc += 1
        hi = self.read_from_bus(self.pc)
        self.pc += 1

        self.addr_abs = (hi << 8) | lo
        return 0

    def ABX(self):
        """ABX - Absolute Addressing with X Register Offset"""
        logging.debug("ABX addressing mode activated")
        lo = self.read_from_bus(self.pc)
        self.pc += 1
        hi = self.read_from_bus(self.pc)
        self.pc += 1

        self.addr_abs = (hi << 8) | lo
        self.addr_abs += self.x_reg

        if (self.addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

    def ABY(self):
        """ABY - Absolute Addressing with Y Register Offset"""
        logging.debug("ABY addressing mode activated")
        lo = self.read_from_bus(self.pc)
        self.pc += 1
        hi = self.read_from_bus(self.pc)
        self.pc += 1

        self.addr_abs = (hi << 8) | lo
        self.addr_abs += self.y_reg

        if (self.addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

    def IND(self):
        """IND - Indirect Addressing Mode"""
        logging.debug("IND addressing mode activated")
        ptr_lo = self.read_from_bus(self.pc)
        self.pc += 1
        ptr_hi = self.read_from_bus(self.pc)
        self.pc += 1
        ptr = (ptr_hi << 8) | ptr_lo

        if ptr_lo == 0x00FF:  # Simulate page boundary hardware bug
            self.addr_abs = (self.read_from_bus(ptr & 0xFF00) << 8) | self.read_from_bus(ptr + 0)
        else:  # Behave normally
            self.addr_abs = (self.read_from_bus(ptr + 1) << 8) | self.read_from_bus(ptr + 0)

        return 0

    def IZX(self):
        """IZX - Indirect Addressing of the Zero page with X Register Offset"""
        logging.debug("IZX addressing mode activated")
        t = self.read_from_bus(self.pc)
        self.pc += 1

        lo = self.read_from_bus(uint16(t + uint16(self.x_reg)) & 0x00FF)
        hi = self.read_from_bus(uint16(t + uint16(self.x_reg) + 1) & 0x00FF)

        self.addr_abs = (hi << 8) | lo

        return 0

    def IZY(self):
        """IZY - Indirect Addressing of the Zero page with Y Register Offset"""
        logging.debug("IZY addressing mode activated")
        t = self.read_from_bus(self.pc)
        self.pc += 1

        lo = self.read_from_bus(t & 0x00FF)
        hi = self.read_from_bus((t + 1) & 0x00FF)

        self.addr_abs = (hi << 8) | lo
        self.addr_abs += self.y_reg

        if (self.addr_abs & 0xFF00) != (hi << 8):
            return 1
        else:
            return 0

        return 0

    # OPERATIONS
    def XXX(self):  # Illegal opcode handler
        return 0

    def ADC(self):  # Add with carry
        return 0

    def AND(self):
        """Logical AND
        Performs a logical AND operation between accumulator value and value fetched from memory
        a = a & fetched"""
        self.fetch()
        self.acc_reg = self.acc_reg & self.fetched
        # Set a Zero status flag if acc_reg == 0
        if self.acc_reg == 0x00:
            self.status_reg = self.status_reg & self.status_map['Z']
        # Set a Negative flag if acc_reg has bit 7 on
        if self.acc_reg & 0x80:
            self.status_reg = self.status_reg & self.status_map['N']

        return 1

    def ASL(self):  # Arithmetic shift left
        return 0

    def BCC(self):
        """Branch if Carry Clear"""
        if not self.status_reg & self.status_map['C']:
            self.cycles += 1
            new_addr = self.pc + self.addr_rel

            if (new_addr & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1

            self.pc = new_addr
        return 0

    def BCS(self):
        """Branch if Carry Bit is set to 1"""
        if self.status_reg & self.status_map['C']:
            self.cycles += 1
            logging.debug("CPU.BCS() - adding 1 CPU cycle")
            new_addr = self.pc + self.addr_rel

            if (new_addr & 0xFF00) != (self.pc & 0xFF00):  # if page-related bits are not the same
                self.cycles += 1
                logging.debug("CPU.BCS() - adding 1 CPU cycle because of paging")

            self.pc = new_addr
        return 0

    def BEQ(self):
        """Branch if Equal --
        If the zero flag is set then add the relative displacement to the program counter to cause a branch to a new
        location."""
        if self.status_reg & self.status_map['Z']:
            self.cycles +=1
            logging.debug("CPU.BEQ() - adding 1 CPU cycle")
            new_addr = self.pc + self.addr_rel

            if (new_addr & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1
                logging.debug("CPU.BEQ() - adding 1 CPU cycle because of paging")

            self.pc = new_addr
        return 0

    def BIT(self):  # Bit  Test
        return 0

    def BMI(self):
        """Branch if Minus --
        If the negative flag is set then add the relative displacement to the program counter to cause a branch to a new
        location."""
        if self.status_reg & self.status_map['N']:
            self.cycles +=1
            logging.debug("CPU.BMI() - adding 1 CPU cycle")
            new_addr = self.pc + self.addr_rel

            if (new_addr & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1
                logging.debug("CPU.BMI() - adding 1 CPU cycle because of paging")

            self.pc = new_addr
        return 0

    def BNE(self):
        """Branch if Not Equal --
        If the zero flag is clear then add the relative displacement to the program counter to cause a branch to a new
        location."""
        if not self.status_reg & self.status_map['Z']:
            self.cycles +=1
            logging.debug("CPU.BNE() - adding 1 CPU cycle")
            new_addr = self.pc + self.addr_rel

            if (new_addr & 0xFF00) != (self.pc & 0xFF00):
                self.cycles += 1
                logging.debug("CPU.BNE() - adding 1 CPU cycle because of paging")

            self.pc = new_addr
        return 0

    def BPL(self):  # Branch if Positive
        return 0

    def BRK(self):  # Force Interrupt (Break)
        return 0

    def BVC(self):  # Branch if Overflow Clear
        return 0

    def BVS(self):  # Branch if Overflow Set
        return 0

    def CLC(self):  # Clear Carry Flag
        return 0

    def CLD(self):  # Clear Decimal Mode
        return 0

    def CLI(self):  # Clear Interrupt Disable
        return 0

    def CLV(self):  # Clear Overflow Flag
        return 0

    def CMP(self):  # Compare
        return 0

    def CPX(self):  # Compare X Register
        return 0

    def CPY(self):  # Compare Y Register
        return 0

    def DEC(self):  # Decrement Memory
        return 0

    def DEX(self):  # Decrement X Register
        return 0

    def DEY(self):  # Decrement Y register
        return 0

    def EOR(self):  # Exclusive OR
        return 0

    def INC(self):  # Increment Memory
        return 0

    def INX(self):  # Increment X Register
        return 0

    def INY(self):  # Increment Y Register
        return 0

    def JMP(self):  # Jump
        return 0

    def JSR(self):  # Jump to Subroutine
        return 0

    def LDA(self):  # Load Accumulator
        return 0

    def LDX(self):  # Load X Register
        return 0

    def LDY(self):  # Load Y register
        return 0

    def LSR(self):  # Logical Shift Right
        return 0

    def NOP(self):  # No Operation (for non-official opcodes)
        return 0

    def ORA(self):  # Logical Inclusive OR
        return 0

    def PHA(self):  # Push Accumulator
        return 0

    def PHP(self):  # Push Processor Status
        return 0

    def PLA(self):  # Pull Accumulator
        return 0

    def PLP(self):  # Pull Processor Status
        return 0

    def ROL(self):  # Rotate Left
        return 0

    def ROR(self):  # Rotate Right
        return 0

    def RTI(self):  # Return from Interrupt
        return 0

    def RTS(self):  # Return from subroutine
        return 0

    def SBC(self):  # Substract with carry
        return 0

    def SEC(self):  # Set Carry Flag
        return 0

    def SED(self):  # Set Decimal Flag
        return 0

    def SEI(self):  # Set Interrupt Disable
        return 0

    def STA(self):  # Store Accumulator
        return 0

    def STX(self):  # Store Register X
        return 0

    def STY(self):  # Store Register Y
        return 0

    def TAX(self):  # Transfer Accumulator to X
        return 0

    def TAY(self):  # Transfer Accumulator to Y
        return 0

    def TSX(self):  # Transfer Stack Pointer to X
        return 0

    def TXA(self):  # Transfer X to Accumulator
        return 0

    def TXS(self):  # Transfer X to Stack Pointer
        return 0

    def TYA(self):  # Transfer Y to Accumulator
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
            logging.debug(f'CPU.clock() - executing instruction {instruction.mnemonic}')

            # Get starting number of cycles
            self.cycles = instruction.cycles
            logging.debug(f"CPU.clock() - setting cycles to: {instruction.cycles}")

            # Address mode and operation can require additional cycles
            additional_cycles_addr_mode = instruction.addr_mode()
            additional_cycles_operation = instruction.operation()
            logging.debug(f"CPU.clock() - adding {additional_cycles_addr_mode & additional_cycles_operation} additional cycles")
            self.cycles += (additional_cycles_addr_mode & additional_cycles_operation)

        self.cycles -= 1
        logging.debug(f"CPU.clock() - clock cycle finished. Remaining cycles: {self.cycles}")

    def illegal_opcode(self):
        pass

    def reset(self):
        pass

    def irq(self):  # Interrupt request signal
        pass

    def nmi(self):  # Non maskable interrupt
        pass

    def fetch(self):
        if self.instructions_lookup[self.opcode].addr_mode is not self.IMP:
            self.fetched = self.read_from_bus(self.addr_abs)
            logging.debug(f'Fetched {self.fetched} from memory address {hex(self.addr_abs)}')
        return self.fetched
