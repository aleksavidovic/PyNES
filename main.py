import argparse
from nes_core.cpu import CPU
from nes_core.bus import Bus


def main():
    # set up command line argument parser
    parser = argparse.ArgumentParser(description='NES Emulator')
    parser.add_argument('rom_path',
                        metavar='R',
                        type=str,
                        help='path to nes rom')
    args = parser.parse_args()

    # TODO: validate rom path is correct
    print(args.rom_path)

    # load rom
    with open(args.rom_path, 'rb') as rom_file:
        lines = rom_file.readlines()

    bus = Bus()
    cpu = CPU()
    cpu.connect_bus(bus)

    cpu.process_instruction(lines[0][0:3])


if __name__ == '__main__':
    main()
