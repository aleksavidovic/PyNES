import unittest
from nes_core.cpu import CPU
from nes_core.exceptions import NoBusConnectedError
from numpy import uint8, uint16


class TestCPU(unittest.TestCase):
    def test_cpu(self):
        cpu = CPU()
        self.assertIsInstance(cpu, CPU)

    def test_write_with_no_bus(self):
        cpu = CPU()
        with self.assertRaises(NoBusConnectedError):
            cpu.write_to_bus(uint16(0), uint8(1))

    def test_read_with_no_bus(self):
        cpu = CPU()
        with self.assertRaises(NoBusConnectedError):
            cpu.read_from_bus(uint16(0))


if __name__ == '__main__':
    unittest.main()
