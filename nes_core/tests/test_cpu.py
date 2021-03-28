import unittest
from nes_core.cpu import CPU
from nes_core.bus import Bus
from nes_core.exceptions import NoBusConnectedError
from numpy import uint8, uint16


class TestCPU(unittest.TestCase):
    def setUp(self) -> None:
        self.cpu = CPU()
        self.bus = Bus()

    def test_cpu(self):
        self.assertIsInstance(self.cpu, CPU)

    def test_write_with_no_bus(self):
        with self.assertRaises(NoBusConnectedError):
            self.cpu.write_to_bus(uint16(0), uint8(1))

    def test_read_with_no_bus(self):
        with self.assertRaises(NoBusConnectedError):
            self.cpu.read_from_bus(uint16(0))

    def test_write_to_bus(self):  # refactor later as an integration test
        self.cpu.connect_bus(self.bus)
        self.cpu.write_to_bus(uint16(0), uint8(1))
        self.assertEqual(self.bus.read(uint16(0)), uint8(1))


class TestCPUInstructions(unittest.TestCase):
    def setUp(self) -> None:
        self.bus = Bus()
        self.cpu = CPU()
        self.cpu.connect_bus(self.bus)

    def test_BCS(self):
        self.bus.write(uint16(0x00FF), uint8(0xB0))  # 0xB0 is code for BCS
        self.bus.write(uint16(0x0100), uint8(0x01))  # address passed
        self.cpu.status_reg = uint8(0b00000001)
        self.cpu.pc = 0x00FF
        self.cpu.clock()
        self.assertEqual(self.cpu.cycles, 2)

    @unittest.expectedFailure
    def test_BCS_with_paging(self):
        self.bus.write(uint16(0x00FE), uint8(0xB0))
        self.bus.write(uint16(0x00FF), uint8(0x01))
        self.cpu.status_reg = uint8(0b00000001)
        self.cpu.pc = 0x00FE
        self.cpu.clock()
        self.assertEqual(self.cpu.cycles, 2)

    @unittest.skip("not implemented")
    def test_BCS_no_carry(self):
        pass

    def test_BRK(self):
        self.bus.write(uint16(0x0000), uint8(0x00))
        self.cpu.clock()
        self.assertEqual(self.cpu.cycles, 6)


if __name__ == '__main__':
    unittest.main()
