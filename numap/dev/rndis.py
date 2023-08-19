'''
Contains class definitions to implement an RNDIS device, i.e. an Ethernet adapter based on Microsoft's standard.

Implemented as per https://learn.microsoft.com/en-us/windows-hardware/drivers/network/usb-802-3-device-sample
'''

from numap.core.usb_class import USBClass
from numap.core.usb_device import USBDevice
from numap.core.usb_configuration import USBConfiguration
from numap.core.usb_interface import USBInterface
from numap.core.usb_endpoint import USBEndpoint
from numap.fuzz.helpers import mutable
class USBRndisClass(USBClass):
    name = 'RndisClass'

    def setup_local_handlers(self):
        self.local_handlers = {
            0x20: self.handle_unknown,
            0x21: self.handle_unknown,
            0x22: self.handle_unknown,
        }

    @mutable('handle_unknown')
    def handle_unknown(self, req):
        # in theory, this should act like
        # https://learn.microsoft.com/en-us/windows-hardware/drivers/network/control-channel-characteristics
        # however, since the (Windows)-PC calls this function, we may already know that the host supports this device

        # self.info(req)
        return b''



class CCInterface(USBInterface):
    name = 'CCInterface'

    def __init__(self, app, phy):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=1,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0008,
                interval=0x01,
                handler=self.handle_data_available
            )
        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=0,
            interface_alternate=0,
            interface_class=0x02,
            interface_subclass=0x02,
            interface_protocol=0xff,
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBRndisClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


class DCInterface(USBInterface):
    name = 'DCInterface'

    def __init__(self, app, phy):
        endpoints = [
            USBEndpoint(
                app=app,
                phy=phy,
                number=2,
                direction=USBEndpoint.direction_in,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0040,
                interval=0,
                handler=self.handle_data_available
            ),
            USBEndpoint(
                app=app,
                phy=phy,
                number=3,
                direction=USBEndpoint.direction_out,
                transfer_type=USBEndpoint.transfer_type_bulk,
                sync_type=USBEndpoint.sync_type_none,
                usage_type=USBEndpoint.usage_type_data,
                max_packet_size=0x0040,
                interval=0,
                handler=None
            )

        ]

        super().__init__(
            app=app,
            phy=phy,
            interface_number=1,
            interface_alternate=0,
            interface_class=0x0a,
            interface_subclass=0x00,
            interface_protocol=0x00,
            interface_string_index=0,
            endpoints=endpoints,
            usb_class=USBRndisClass(app, phy)
        )

    @mutable('handle_data_available')
    def handle_data_available(self, data):
        self.info(data)


class USBRndisDevice(USBDevice):
    name = 'RndisDevice'

    def __init__(self, app, phy):
        super().__init__(
            app=app,
            phy=phy,
            device_class=USBClass.CDC,
            device_subclass=0,
            protocol_rel_num=0,
            max_packet_size_ep0=64,
            vendor_id=0x2001,  # D-Link Corp.
            product_id=0x4a00,  # DUB-1312 Gigabit Ethernet Adapter
            device_rev=1,
            manufacturer_string='numap Inc.',
            product_string='numap RNDIS Network Interface',
            serial_number_string='0123456789-1337',
            configurations=[
                USBConfiguration(
                    app=app,
                    phy=phy,
                    index=1,
                    string='RNDIS',
                    interfaces=[
                        CCInterface(app, phy),
                        DCInterface(app, phy)
                    ]
                )
            ]
        )


usb_device = USBRndisDevice
