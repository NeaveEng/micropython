#!/usr/bin/env python
"""Creates the pin file for the RP2."""

import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "../../../tools"))
import boardgen

# This is NUM_BANK0_GPIOS. Pin indices are 0 to 29 (inclusive).
NUM_GPIOS = 30
# Up to 10 additional extended pins (e.g. via the wifi chip).
NUM_EXT_GPIOS = 10


class Rp2Pin(boardgen.Pin):
    def __init__(self, cpu_pin_name):
        super().__init__(cpu_pin_name)
        self._afs = []

        if self.name().startswith("EXT_"):
            self._index = None
            self._ext_index = int(self.name()[8:])  # "EXT_GPIOn"
        else:
            self._index = int(self.name()[4:])  # "GPIOn"
            self._ext_index = None

    # Required by NumericPinGenerator.
    def index(self):
        return self._index

    # Use the PIN() macro defined in rp2_prefix.c for defining the pin
    # objects.
    def definition(self):
        if self._index is not None:
            return "PIN({:d}, GPIO{:d}, 0, {:d}, pin_GPIO{:d}_af)".format(
                self._index, self._index, len(self._afs), self.index()
            )
        else:
            return "PIN({:d}, EXT_GPIO{:d}, 1, 0, NULL)".format(self._ext_index, self._ext_index)

    # External pins need to be mutable (because they track the output state).
    def is_const(self):
        return self._index is not None

    # Add conditional macros only around the external pins based on how many
    # are enabled.
    def enable_macro(self):
        if self._ext_index is not None:
            return "(MICROPY_HW_PIN_EXT_COUNT > {:d})".format(self._ext_index)

    def add_af(self, af_idx, _af_name, af):
        if self._index is None:
            raise boardgen.PinGeneratorError(
                "Cannot add AF for ext pin '{:s}'".format(self.name())
            )

        # <af><unit>_<pin>
        m = re.match("([A-Z][A-Z0-9][A-Z]+)(([0-9]+)(_.*)?)?", af)
        af_fn = m.group(1)
        af_unit = int(m.group(3)) if m.group(3) is not None else 0
        if af_fn == "PIO":
            # Pins can be either PIO unit (unlike, say, I2C where a
            # pin can only be I2C0 _or_ I2C1, both sharing the same AF
            # index), so each PIO unit has a distinct AF index.
            af_fn = "{:s}{:d}".format(af_fn, af_unit)
        self._afs.append((af_idx + 1, af_fn, af_unit, af))


class Pins(object):
    def __init__(self):
        self.cpu_pins = []  # list of NamedPin objects
        self.board_pins = []  # list of NamedPin objects
        self.ext_pins = []  # list of NamedPin objects
        for i in range(0, 32):
            self.ext_pins.append(NamedPin("EXT_GPIO{:d}".format(i), Pin(i, True)))

    def find_pin(self, pin_name):
        for pin in self.cpu_pins:
            if pin.name() == pin_name:
                return pin.pin()

        for pin in self.ext_pins:
            if pin.name() == pin_name:
                return pin.pin()

    def parse_af_file(self, filename, pinname_col, af_col):
        with open(filename, "r") as csvfile:
            rows = csv.reader(csvfile)
            for row in rows:
                try:
                    pin_num = parse_pin(row[pinname_col])
                except Exception:
                    # import traceback; traceback.print_exc()
                    continue
                pin = Pin(pin_num)
                for af_idx in range(af_col, len(row)):
                    if af_idx >= af_col:
                        pin.parse_af(af_idx, row[af_idx])
                self.cpu_pins.append(NamedPin(pin.cpu_pin_name(), pin))

    def parse_board_file(self, filename):
        with open(filename, "r") as csvfile:
            rows = csv.reader(csvfile)
            for row in rows:
                if len(row) == 0 or row[0].startswith("#"):
                    # Skip empty lines, and lines starting with "#"
                    continue
                if len(row) != 2:
                    raise ValueError("Expecting two entries in a row")

                cpu_pin_name = row[1]
                try:
                    parse_pin(cpu_pin_name)
                except:
                    # import traceback; traceback.print_exc()
                    continue
                pin = self.find_pin(cpu_pin_name)
                if pin:
                    pin.set_is_board_pin()
                    if row[0]:  # Only add board pins that have a name
                        self.board_pins.append(NamedPin(row[0], pin))

    def print_table(self, label, named_pins):
        print("")
        print("const machine_pin_obj_t *machine_pin_{:s}_pins[] = {{".format(label))
        for pin in named_pins:
            if not pin.pin().is_ext:
                print("    &pin_{},".format(pin.name()))
        print("};")
        print("")

    def print_named(self, label, named_pins):
        print("")
        print(
            "STATIC const mp_rom_map_elem_t pin_{:s}_pins_locals_dict_table[] = {{".format(label)
        )
        for named_pin in named_pins:
            pin = named_pin.pin()
            if pin.is_ext:
                print("  #if (MICROPY_HW_PIN_EXT_COUNT > {:d})".format(pin.pin))
            print(
                "const machine_pin_af_obj_t pin_GPIO{:d}_af[] = {{".format(self.index()),
                file=out_source,
            )
            for af_idx, af_fn, af_unit, af in self._afs:
                print(
                    "    AF({:d}, {:4s}, {:d}), // {:s}".format(af_idx, af_fn, af_unit, af),
                    file=out_source,
                )
            print("};", file=out_source)
            print(file=out_source)

    # rp2 cpu names must be "GPIOn" or "EXT_GPIOn".
    @staticmethod
    def validate_cpu_pin_name(cpu_pin_name):
        boardgen.Pin.validate_cpu_pin_name(cpu_pin_name)

        if cpu_pin_name.startswith("GPIO") and cpu_pin_name[4:].isnumeric():
            if not (0 <= int(cpu_pin_name[4:]) < NUM_GPIOS):
                raise boardgen.PinGeneratorError("Unknown cpu pin '{}'".format(cpu_pin_name))
        elif cpu_pin_name.startswith("EXT_GPIO") and cpu_pin_name[8:].isnumeric():
            if not (0 <= int(cpu_pin_name[8:]) < NUM_EXT_GPIOS):
                raise boardgen.PinGeneratorError("Unknown ext pin '{}'".format(cpu_pin_name))
        else:
            raise boardgen.PinGeneratorError(
                "Invalid cpu pin name '{}', must be 'GPIOn' or 'EXT_GPIOn'".format(cpu_pin_name)
            )


class Rp2PinGenerator(boardgen.NumericPinGenerator):
    def __init__(self):
        # Use custom pin type above, and also enable the --af-csv argument.
        super().__init__(
            pin_type=Rp2Pin,
            enable_af=True,
        )

        # Pre-define the pins (i.e. don't require them to be listed in pins.csv).
        for i in range(NUM_GPIOS):
            self.add_cpu_pin("GPIO{}".format(i))
        for i in range(NUM_EXT_GPIOS):
            self.add_cpu_pin("EXT_GPIO{}".format(i))

    # Provided by pico-sdk.
    def cpu_table_size(self):
        return "NUM_BANK0_GPIOS"

    # Only use pre-defined cpu pins (do not let board.csv create them).
    def find_pin_by_cpu_pin_name(self, cpu_pin_name, create=True):
        return super().find_pin_by_cpu_pin_name(cpu_pin_name, create=False)

    # NumericPinGenerator doesn't include the cpu dict by default (only the
    # board dict), so add that to the output for rp2.
    def print_source(self, out_source):
        super().print_source(out_source)
        self.print_cpu_locals_dict(out_source)


if __name__ == "__main__":
    Rp2PinGenerator().main()
