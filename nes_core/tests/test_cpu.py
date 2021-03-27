import unittest
from nes_core.cpu import CPU


class TestCPU(unittest.TestCase):
    def test_cpu(self):
        cpu = CPU()
        self.assertIsInstance(cpu, CPU)


if __name__ == '__main__':
    unittest.main()
