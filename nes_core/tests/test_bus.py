import unittest
from numpy import uint8, uint16
from nes_core.bus import Bus


class TestBus(unittest.TestCase):
    def test_bus(self):
        bus = Bus()
        self.assertIsInstance(bus, Bus)

    def test_bus_ram_size(self):
        bus = Bus()
        self.assertEqual(len(bus.ram), 64 * 1024)

    def test_bus_ram_all_initial_zeroes(self):
        bus = Bus()
        self.assertEqual(bus.ram, [0] * (64 * 1024))

    def test_write(self):
        bus = Bus()
        bus.write(uint16(0), uint8(4))
        self.assertEqual(bus.ram[0], uint8(4))

    def test_write_bad_type(self):
        bus = Bus()
        with self.assertRaises(TypeError):
            bus.write(uint16(0), str(4))

    def test_write_address_out_of_range(self):
        bus = Bus()
        with self.assertRaises(ValueError):
            bus.write(0xFFFFF, uint8(0))

    def test_address_in_range(self):
        bus = Bus()
        self.assertTrue(bus.address_in_range(uint16(0xAAAA)))

    def test_address_in_range_invalid_address(self):
        bus = Bus()
        self.assertFalse(bus.address_in_range(0xFFFF + 1))


if __name__ == '__main__':
    unittest.main()
