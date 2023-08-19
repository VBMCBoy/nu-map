'''
Explore and modify USB Strings.

Usage:
    numap-strings [-P PHY_INFO] [-q] [-v LEVEL]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose LEVEL          verbosity level, higher is more verbose [default: 0]
    -q --quiet                  quiet mode. only print warning/error messages

Physical layer:
    fd:<serial_port>            use facedancer connected to given serial port
    gadgetfs                    use gadgetfs (requires mounting of gadgetfs beforehand)

Example:
    numapscan -P fd:/dev/ttyUSB0 -q
'''
from numap.apps.base import NumapApp


# maps the descriptors of devices to indices in the string array
# TODO this is kinda fragile...
STRING_LOCATIONS = {
    'billboard': {
        'Manufacturer String': 0,
        'Product String': 1,
        'Serial Number String': 2,
        'Configuration String': 3,
        'Billboard Additional Info String': 4,
        'Alternate Mode String': 5,
    },
    'printer': {
        'Manufacturer String': 0,
        'Product String': 1,
        'Serial Number String': 2,
        'Configuration String': 3,
        'Device ID (insert as Python dictionary, will be automatically formatted, bytes are passed as-is; unlimited length)': 4
    },
}

STRING_LOCATIONS |= {name: {
    'Manufacturer String': 0,
    'Product String': 1,
    'Serial Number String': 2,
    'Configuration String': 3
} for name in ['audio', 'cdc_acm', 'cdc_dl', 'cdc_ecm', 'cdc_eem', 'cdc_ncm', 'ftdi', 'hub', 'keyboard', 'mass_storage', 'mtp', 'rndis', 'smartcard']}

STRING_LOCATIONS |= {name: {
    'Manufacturer String': 0,
    'Product String': 1,
    'Serial Number String': 2,
} for name in ['bluetooth_cypress', 'wifi_qualcomm', 'wifi_realtek']}

class NumapStringsApp(NumapApp):

    def __init__(self, options):
        super(NumapStringsApp, self).__init__(options)
        self.current_usb_function_supported = False
        self.was_configured = False
        self.start_time = 0
        self.reasons = set()

    def run(self):
        phy = self.load_phy(self.options['--phy'])

        while True:
            print('Available devices:')
            for i, name in enumerate(self.umap_classes):
                print(f'{i} ({name}): {self.umap_class_dict[name][1]}')

            dev_id = input('Select a device or "e" to exit: ')
            if dev_id.lower() == 'e':
                exit(0)
            try:
                dev_id = int(dev_id)
            except:
                print('Could not parse selection as integer.')
                continue
            if dev_id in range(len(self.umap_classes)):
                dev = self.load_device(self.umap_classes[dev_id], phy)
                print(f'Loaded {self.umap_classes[dev_id]}')
                dev_name = self.umap_classes[dev_id]
            else:
                print('Selection is not valid.')
                continue

            while True:
                print('Available strings:')
                for name, location in STRING_LOCATIONS[dev_name].items():
                    print(f'{location} {name}:\n\t"{dev.strings[location]}"')

                idx = input('Select string to edit, "s" to start the emulation, "b" to go back to device selection, or "e" to exit: ')
                if idx == 'b':
                    break
                elif idx == 's':
                    dev.connect()
                    try:
                        dev.run()
                    except KeyboardInterrupt:
                        dev.disconnect()
                elif idx == 'e':
                    exit(0)
                else:
                    try:
                        idx = int(idx)
                    except:
                        print('Could not parse selection as integer.')
                        continue
                    if idx in range(len(dev.strings)):
                        string_name = [x for x, y in STRING_LOCATIONS[dev_name].items() if y == idx][0]
                        print(f'Selected {string_name}')
                        sel = input('Input bytes as hex? Otherwise string will be converted to UTF-16 [y/N] ')
                        if not sel or sel.lower() == 'n':
                            use_bytes = False
                        elif sel.lower() == 'y':
                            use_bytes = True
                        else:
                            print('Invalid selection.')
                            continue
                        data = input('Data: ')
                        if not (string_name.startswith('Device ID') and dev_name == 'printer'):  # printer ID can be arbitrarily large
                            if not use_bytes:
                                if len(data.encode('UTF-16')) > 255:
                                    print(f'A String Descriptor can be at most 0xff bytes long when encoded as UTF-16 (got {len(data.encode("UTF-16"))})')
                                    continue
                            else:
                                data = bytes.fromhex(data)
                                if len(data) > 255:
                                    print(f'A String Descriptor can be at most 0xff bytes long (got {len(data)})')
                                    continue
                        dev.strings[idx] = data
                        continue
                    else:
                        print('Selection is not valid.')
                        continue


    def should_stop_phy(self):
        return False


def main():
    app = NumapStringsApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
