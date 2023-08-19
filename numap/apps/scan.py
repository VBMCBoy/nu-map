'''
Scan device support in USB host

Usage:
    numapscan [-P=PHY_INFO] [-q] [-v ...]

Options:
    -P --phy PHY_INFO           physical layer info, see list below
    -v --verbose                verbosity level
    -q --quiet                  quiet mode. only print warning/error messages

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

    def run(self):
        self.logger.always('Scanning host for supported devices')
        phy = self.load_phy(self.options['--phy'])
        supported = []
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
            self.current_usb_function_supported = False
            time.sleep(2)

        if supported:
            self.logger.always('---------------------------------')
            self.logger.always('Found %s supported device(s):' % (len(supported)))
            for i, device_name in enumerate(supported):
                self.logger.always(f'{i+1}. {device_name} ({self.umap_class_dict[device_name][1]})')

    def should_stop_phy(self):
        # if self.current_usb_function_supported:
        #     self.logger.debug('Current USB device is supported, stopping phy')
        #     return True
        stop_phy = False
        passed = int(time.time() - self.start_time)
        if passed > 5:
            self.logger.info('have been waiting long enough (over %d secs.), disconnect' % (passed))
            stop_phy = True
        return stop_phy


def main():
    app = NumapScanApp(__doc__)
    app.run()


if __name__ == '__main__':
    main()
