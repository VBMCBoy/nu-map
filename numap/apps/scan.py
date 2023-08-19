'''
Scan device support in USB host

Usage:
    numapscan [-P PHY_INFO] [-q] [-T] [-t TIMEOUT] [-v LEVEL] [-d DEVICE...] [-i DEVICE...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose LEVEL          verbosity level, higher is more verbose [default: 0]
    -q --quiet                  quiet mode. only print warning/error messages
    -t --timeout TIMEOUT        timeout of each device test in seconds [default: 5]
    -T --always-timeout         keep emulating the device until the timeout is reached, regardless of support
    -d --device DEVICE          test only the specified device(s)
    -i --ignore DEVICE          do not test the specified device(s)
                                Ignored devices override requested (-d) devices.

Physical layer:
    fd:<serial_port>        use facedancer connected to given serial port
    gadgetfs                use gadgetfs (requires mounting of gadgetfs beforehand)

Example:
    numapscan -P fd:/dev/ttyUSB0 -q
'''
import time
import traceback
from numap.apps.base import NumapApp


class NumapScanApp(NumapApp):

    def __init__(self, options):
        super(NumapScanApp, self).__init__(options)
        self.current_usb_function_supported = False
        self.was_configured = False
        self.start_time = 0
        self.reasons = set()

    def usb_function_supported(self, reason=None):
        '''
        Callback from a USB device, notifying that the current USB device
        is supported by the host.

        :param reason: reason why we decided it is supported (default: None)
        '''
        self.current_usb_function_supported = True
        if reason:
            self.reasons.add(reason)

    def usb_configuration_occurred(self):
        '''
        Callback from a USB device, notifying that the current USB device
        was configured by the host (a configuration was selected).

        This does not necessarily mean that the device is supported.
        However, under Windows, devices without a driver are not configured.
        '''

        self.was_configured = True

    def run(self):
        self.logger.always('Scanning host for supported devices')
        phy = self.load_phy(self.options['--phy'])
        supported = []
        unsupported = []

        if self.options['--device']:
            if set(self.options['--device']).issubset(set(self.umap_classes)):
                self.umap_classes = list(set(self.options['--device']))
            else:
                self.logger.error(f'Unknown requested devices found: {set(self.options["--device"]).difference(set(self.umap_classes))}')
                self.logger.error(f'Available devices: {self.umap_classes}')
                exit(1)

        if self.options['--ignore']:
            if set(self.options['--ignore']).issubset(set(self.umap_classes)):
                self.umap_classes = list(set(self.umap_classes) - set(self.options['--ignore']))
            else:
                self.logger.error(f'Unknown ignored devices found: {set(self.options["--ignore"]).difference(set(self.umap_classes))}\n'
                                  f'Available devices are: {self.umap_classes}')
                exit(1)

        for device_name in self.umap_classes:
            self.logger.always('Testing support: %s' % (device_name))
            try:
                self.start_time = time.time()
                device = self.load_device(device_name, phy)
                device.connect()
                device.run()
                device.disconnect()
            except:
                self.logger.error(traceback.format_exc())
            phy.disconnect()
            if self.current_usb_function_supported:
                self.logger.always('Device is SUPPORTED')
                self.logger.always(self.reasons)
                supported.append(device_name)
            else:
                self.logger.always('Device is UNSUPPORTED')
                if self.was_configured:
                    self.logger.always('but was configured')
                unsupported.append((device_name, self.was_configured))
            self.current_usb_function_supported = False
            self.was_configured = False
            time.sleep(2)

        if supported:
            self.logger.always('---------------------------------')
            self.logger.always('Found %s supported device(s):' % (len(supported)))
            for i, device_name in enumerate(supported):
                self.logger.always(f'{i+1}. {device_name} ({self.umap_class_dict[device_name][1]})')
        if unsupported:
            self.logger.always('---------------------------------')
            self.logger.always('Found %s unsupported device(s):' % (len(unsupported)))
            for i, device_name in enumerate(unsupported):
                self.logger.always(f'{i+1}. {device_name[0]} ({self.umap_class_dict[device_name[0]][1]}){" (configured)" if device_name[1] else ""}')

    def should_stop_phy(self):
        if self.current_usb_function_supported and not self.options.get('--always-timeout', False):
            self.logger.debug('Current USB device is supported, stopping phy')
            return True
        stop_phy = False
        passed = int(time.time() - self.start_time)
        if passed > int(self.options['--timeout']):
            self.logger.info('have been waiting long enough (over %d secs.), disconnect' % (passed))
            stop_phy = True
        return stop_phy


def main():
    app = NumapScanApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
