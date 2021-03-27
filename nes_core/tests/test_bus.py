import unittest
from nes_core.bus import Bus
from nes_core.cpu import CPU


class TestBus(unittest.TestCase):
    def test_bus(self):
        cpu = CPU()
        bus = Bus(cpu)
        self.assertIsInstance(bus, Bus)

    def test_bus_ram_size(self):
        cpu = CPU()
        bus = Bus(cpu)
        self.assertEqual(len(bus.ram), 64 * 1024)

    def test_bus_ram_all_initial_zeroes(self):
        cpu = CPU()
        bus = Bus(cpu)
        self.assertEqual(bus.ram, [0] * (64 * 1024))


if __name__ == '__main__':
    unittest.main()
