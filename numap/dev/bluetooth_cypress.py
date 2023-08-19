'''
Contains class definitions to implement a Bluetooth Cypress device, i.e. a Bluetooth adapter.

Implemented as per the lsusb output of a 04b4:f901 Cypress Semiconductor Corp. CYW20704A2.
'''

from numap.core.usb_class import USBClass
from numap.core.usb_device import USBDevice
from numap.core.usb_configuration import USBConfiguration
from numap.core.usb_interface import USBInterface
from numap.core.usb_endpoint import USBEndpoint
from numap.fuzz.helpers import mutable


class USBBluetoothCypressClass(USBClass):
    name = 'BluetoothCypressClass'

    def setup_local_handlers(self):
        self.local_handlers = {
            x: self.handle_unknown for x in range(0, 256)
        }

    @mutable('handle_unknown')
    def handle_unknown(self, req):
        return b''


class DataInterface(USBInterface):
    name = 'DataInterface'

    def __init__(self, app, phy, alternate_setting, max_packet_size):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=3,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_isochronous,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=max_packet_size,
                interval=1,
                handler=self.handle_data_available,
                usb_class=USBBluetoothCypressClass(app, phy)
        ),
            USBEndpoint(
                app=app,
                phy=phy,
                number=3,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_isochronous,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=max_packet_size,
                interval=1,
                handler=None,
                usb_class=USBBluetoothCypressClass(app, phy)
            )

        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=1,
            interface_alternate=alternate_setting,
            interface_class=0xe0,  # Wireless
            interface_subclass=0x01,  # Radio Frequency
            interface_protocol=0x01,  # Bluetooth
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBBluetoothCypressClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


class SuperDataInterface(USBInterface):
    name = 'SuperDataInterface'

    def __init__(self, app, phy):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=1,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_interrupt,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0010,
                interval=1,
                handler=self.handle_data_available,
                usb_class=USBBluetoothCypressClass(app, phy)
            ),
            USBEndpoint(
                app=app,
                phy=phy,
                number=2,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0040,
                interval=1,
                handler=self.handle_data_available,
                usb_class=USBBluetoothCypressClass(app, phy)
        ),
            USBEndpoint(
                app=app,
                phy=phy,
                number=2,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0040,
                interval=1,
                handler=None,
                usb_class=USBBluetoothCypressClass(app, phy)

            )
        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=0,
            interface_alternate=0,
            interface_class=0xe0,  # Wireless
            interface_subclass=0x01,  # Radio Frequency
            interface_protocol=0x01,  # Bluetooth
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBBluetoothCypressClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


class VendorSpecificInterface(USBInterface):
    name = 'VendorSpecificInterface'

    def __init__(self, app, phy):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=4,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0020,
                interval=1,
                handler=self.handle_data_available,
                usb_class=USBBluetoothCypressClass(app, phy)
            ),
            USBEndpoint(
                app=app,
                phy=phy,
                number=4,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0020,
                interval=1,
                handler=self.handle_data_available,
                usb_class=USBBluetoothCypressClass(app, phy)
            )
        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=2,
            interface_alternate=0,
            interface_class=0xff,  # Vendor Specific
            interface_subclass=0xff,  # Vendor Specific
            interface_protocol=0xff,  # Vendor Specific
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBBluetoothCypressClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


# The device additionally contains a DFU Interface, but I believe we can't emulate this (yet?)

class USBBluetoothCypressDevice(USBDevice):
    name = 'BluetoothCypressDevice'

    def __init__(self, app, phy):
        super().__init__(
            app=app,
            phy=phy,
            device_class=USBClass.WirelessController,
            device_subclass=1,  # Radio Frequency
            protocol_rel_num=1,  # Bluetooth
            max_packet_size_ep0=64,
            vendor_id=0x04b4,  # Cypress Semiconductor Corp.
            product_id=0xf901,
            device_rev=1,
            manufacturer_string='Cypress Semi',
            product_string='CYW20704A2',
            serial_number_string='0016A44CB785',
            configurations=[
                USBConfiguration(
                    app=app,
                    phy=phy,
                    index=1,
                    string='',
                    interfaces=[
                        SuperDataInterface(app, phy),
                        DataInterface(app, phy, 0, 0),
                        DataInterface(app, phy, 1, 9),
                        DataInterface(app, phy, 2, 0x11),
                        DataInterface(app, phy, 3, 0x19),
                        DataInterface(app, phy, 4, 0x21),
                        DataInterface(app, phy, 5, 0x31),
                        VendorSpecificInterface(app, phy)
                    ],
                )
            ],
            usb_class=USBBluetoothCypressClass(app, phy)
        )


usb_device = USBBluetoothCypressDevice
