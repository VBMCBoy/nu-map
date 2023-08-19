'''
Try to detect OS based on the USB traffic.
Not implemented yet.

Usage:
    numapdetect [-P=PHY_INFO] [-q] [-v ...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose                verbosity level
    -q --quiet                  quiet mode. only print warning/error messages

Physical layer:
    fd:<serial_port>        use facedancer connected to given serial port
    gadgetfs                use gadgetfs (requires mounting of gadgetfs beforehand)

Example:
    numapdetect -P fd:/dev/ttyUSB0 -q
'''
from __future__ import annotations  # so we can better use type hints, see https://stackoverflow.com/a/35617812

import time
from typing import Type

import usb.core

from Facedancer.facedancer.USBClass import USBClass
from Facedancer.facedancer.USBDevice import USBDevice
from numap.apps.base import NumapApp

from numap.apps.fingerprints import DEVICES, FINGERPRINTS, OS

def test(fun):
    def wrapper(req):
        # TODO unfortunately this does not keep the original name (becomes `wrapper` instead...)
        # print(fun.__name__, hex(req.length)[2:],
        #       req.data if req.data else '', req.get_request_number_string(), req.get_value_string(), sep='\t')
        return fun(req)
    return wrapper


def get_components(base_class: Type[USBClass], base_dev: Type[USBDevice]) -> tuple[Type[TestDevice], Type[TestClass]]:
    assert base_class is not None
    assert base_dev is not None

    class TestDevice(base_dev):
        def handle_request(self, request):
            #       print(request)
            #       print(request.length)
            if request.get_request_number_string() == 'SET_CONFIGURATION':
                self.app.configuration_finished = True

            self.app.requests.append(request)
            if not self.app.configuration_finished:
                self.app.configuration_requests.append(request)

            super().handle_request(request)

        def setup_request_handlers(self):
            super().setup_request_handlers()
            self.request_handlers = {i: test(fun) for (i, fun) in self.request_handlers.items()}

    class TestClass(base_class):
        def setup_local_handlers(self):
            super().setup_local_handlers()
            self.local_handlers = {i: test(fun) for (i, fun) in self.local_handlers.items()}

    return tuple([TestDevice, TestClass])


class NumapDetectOSApp(NumapApp):
    def __init__(self, options):
        super().__init__(options)
        self.start_time = time.time()
        self.requests = []
        self.configuration_requests = []
        self.configuration_finished = False
        self.combined_results = {}

    def run(self):
        print(
            f'Devices sometimes hang during OS detection. Reattach the GreatFET to the host to continue with the next device.')
        phy = self.load_phy(self.options['--phy'])
        for device_name, base_dev, base_class in DEVICES:
            # reset everything
            self.start_time = time.time()
            self.requests = []
            self.configuration_requests = []
            self.configuration_finished = False

            print(f'Testing {device_name} ({self.umap_class_dict[device_name][1]})...')
            device, cls = get_components(base_class=base_class, base_dev=base_dev)
            device = device(self, phy)
            if device_name == 'mass_storage':
                device.scsi_device.handlers = {i: test(fun) for (i, fun) in device.scsi_device.handlers.items()}
                cls = cls(self, phy, device.scsi_device)
            else:
                cls = cls(self, phy)
            device.configurations[0].interfaces[0].usb_class = cls
            device.connect()
            try:
                device.run()
                device.disconnect()
            except usb.core.USBError as e:
                print(f'There was an error: {e}')
                TIMEOUT = 5
                print(
                    f'Please reattach the GreatFET to the host within {TIMEOUT} seconds. This device test may be incomplete.')
                time.sleep(TIMEOUT)
            if self.requests:
                print()
                results = []
                for dev, lamb in FINGERPRINTS.items():
                    dev_types, desc = dev
                    if device_name in dev_types or dev_types == 'ANY':
                        res = lamb(self.requests, self.configuration_requests)
                        for r in res:
                            if r < 0:
                                print(f'not {OS(-r).name} ({desc})')
                            else:
                                print(f'{r.name} ({desc})')
                        results.append(res)
                        if device_name not in self.combined_results.keys():
                            self.combined_results[device_name] = {}
                        self.combined_results[device_name][desc] = res
                print('------------------------')
            else:
                print(
                    f'No requests received. Try reconnecting the GF One. Are you sure the host supports {device_name} devices?')
            time.sleep(2)

        counts = {}
        for device_name, results in self.combined_results.items():
            print(f'{device_name} ({self.umap_class_dict[device_name][1]}):')
            for ttest, result in results.items():
                print('\t', ttest)
                for res in result:
                    os = OS(res).name if res >= 0 else f'not {OS(-res).name}'
                    print('\t' * 2, os)
                    if os not in counts.keys():
                        counts[os] = 0
                    counts[os] += 1
        print('------------------------')
        print('Overall:')
        for os, number in counts.items():
            print(os, number)

    def should_stop_phy(self):
        stop_phy = False
        passed = int(time.time() - self.start_time)
        if passed > 8:  # or self.configuration_finished:
            self.logger.info('have been waiting long enough (over %d secs.), disconnect' % (passed))
            stop_phy = True
        return stop_phy


def main():
    app = NumapDetectOSApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
