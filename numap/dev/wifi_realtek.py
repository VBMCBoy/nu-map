'''
Contains class definitions to implement a Realtek WiFi device.

Implemented as per the lsusb output of a 0bda:8812 Realtek Semiconductor Corp. TRL8812AU 802.11a/b/g/n/ac 2T2R DB WLAN Adapter.
'''

from numap.core.usb_class import USBClass
from numap.core.usb_device import USBDevice
from numap.core.usb_configuration import USBConfiguration
from numap.core.usb_interface import USBInterface
from numap.core.usb_endpoint import USBEndpoint
from numap.core.usb_vendor import USBVendor
from numap.fuzz.helpers import mutable


class USBRealtekWifiVendor(USBVendor):
    name = "USB FTDI vendor"

    def setup_local_handlers(self):
        self.local_handlers = { i: self.ignore_request for i in range(0, 256) }

    def ignore_request(self, req):
        self.device.maxusb_app.send_on_endpoint(0, b'')

class USBRealtekWifiClass(USBClass):
    name = 'RealtekWifiClass'

    def setup_local_handlers(self):
        self.local_handlers = {
            x: self.handle_unknown for x in range(0, 256)
        }

    @mutable('handle_unknown')
    def handle_unknown(self, req):
        return b''


class USBRealtekWifiInterface(USBInterface):
    name = 'RealtekWifiInterface'

    def __init__(self, app, phy):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=number,
                direction=direction,
                transfer_type=transfer_type,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=max_packet_size,
                interval=interval,
                handler=self.handle_data_available,
                usb_class=USBRealtekWifiClass(app, phy)
            ) for number, direction, transfer_type, max_packet_size, interval in
            [
                (1, USBEndpoint.direction_in, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (2, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (3, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (4, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (5, USBEndpoint.direction_in, USBEndpoint.transfer_type_interrupt, 0x40, 1)
            ]

        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=0,
            interface_alternate=0,
            interface_class=0xff,  # Vendor Specific
            interface_subclass=0xff,  # Vendor Specific
            interface_protocol=0xff,  # Vendor Specific
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBRealtekWifiClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


# The device additionally contains a DFU Interface, but I believe we can't emulate this (yet?)

class USBRealtekWifiDevice(USBDevice):
    name = 'RealtekWifiDevice'

    def __init__(self, app, phy):
        super().__init__(
            app=app,
            phy=phy,
            device_class=0,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=0x0bda,  # Realtek Semiconductor Corp.
            product_id=0x8812,  # RTL8812AU 802.11a/b/g/n/ac 2T2R DB WLAN Adapter
            device_rev=1,
            manufacturer_string='Realtek',
            product_string='802.11n NIC',
            serial_number_string='123456',  # actual value
            configurations=[
                USBConfiguration(
                    app=app,
                    phy=phy,
                    index=1,
                    string='',
                    interfaces=[
                        USBRealtekWifiInterface(app, phy)
                    ],
                )
            ],
            usb_class=USBRealtekWifiClass(app, phy),
            usb_vendor=USBRealtekWifiVendor(app, phy)
        )


usb_device = USBRealtekWifiDevice
