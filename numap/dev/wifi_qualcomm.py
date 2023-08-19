'''
Contains class definitions to implement a Qualcomm Atheros Wifi Device.

Implemented as per the lsusb output of a 0cf3:9271 Qualcomm Atheros Communications AR9271 902.11n.
'''

from numap.core.usb_class import USBClass
from numap.core.usb_device import USBDevice
from numap.core.usb_configuration import USBConfiguration
from numap.core.usb_interface import USBInterface
from numap.core.usb_endpoint import USBEndpoint
from numap.core.usb_vendor import USBVendor
from numap.fuzz.helpers import mutable


class USBQualcommWifiClass(USBClass):
    name = 'QualcommWifiClass'

    def setup_local_handlers(self):
        self.local_handlers = {
            x: self.handle_unknown for x in range(0, 256)
        }

    @mutable('handle_unknown')
    def handle_unknown(self, req):
        return b''


class USBQualcommWifiVendor(USBVendor):
    name = 'QualcommWifiVendor'

    def __init__(self, app, phy):
        super().__init__(app, phy)

    def setup_local_handlers(self):
        self.local_handlers = {
            i: self.handle_anything for i in range(0, 256)
        }

    @mutable('qualcommwifi_handle_anything')
    def handle_anything(self, req):
        return b''


class USBQualcommWifiInterface(USBInterface):
    name = 'QualcommWifiInterface'

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
                usb_class=USBQualcommWifiClass(app, phy),
                usb_vendor=USBQualcommWifiVendor(app, phy)
            ) for number, direction, transfer_type, max_packet_size, interval in
            [
                (1, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (2, USBEndpoint.direction_in, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (3, USBEndpoint.direction_in, USBEndpoint.transfer_type_interrupt, 0x40, 1),
                (4, USBEndpoint.direction_out, USBEndpoint.transfer_type_interrupt, 0x40, 1),
                (5, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0),
                (6, USBEndpoint.direction_out, USBEndpoint.transfer_type_bulk, 0x200, 0)
            ]

        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=0,
            interface_alternate=0,
            interface_class=0xff,  # Vendor Specific
            interface_subclass=0,
            interface_protocol=0,
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBQualcommWifiClass(app, phy),
            usb_vendor=USBQualcommWifiVendor(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


class USBQualcommWifiDevice(USBDevice):
    name = 'QualcommWifiDevice'

    def __init__(self, app, phy):
        super().__init__(
            app=app,
            phy=phy,
            device_class=0xff,
            device_subclass=0xff,
            protocol_rel_num=0xff,
            max_packet_size_ep0=64,
            vendor_id=0x0cf3,  # Qualcomm Atheros Communications
            product_id=0x9271,  # AR9271 802.11n
            device_rev=1,
            manufacturer_string='ATHEROS',
            product_string='USB2.0 WLAN',
            serial_number_string='12345',  # actual value
            configurations=[
                USBConfiguration(
                    app=app,
                    phy=phy,
                    index=1,
                    string='',
                    interfaces=[
                        USBQualcommWifiInterface(app, phy)
                    ],
                )
            ],
            usb_class=USBQualcommWifiClass(app, phy),
            usb_vendor=USBQualcommWifiVendor(app, phy)
        )


usb_device = USBQualcommWifiDevice
