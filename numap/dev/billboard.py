'''
USB Billboard implementation

Based on USB_Billboard_Revision_1_0_20140801.pdf
All references in this script ar to this pdf.
'''
import struct

from numap.core.usb_interface import USBInterface
from numap.core.usb_device import USBDevice
from numap.core.usb_class import USBClass
from numap.core.usb_configuration import USBConfiguration
from numap.core.usb_bos import USBBinaryObjectStore
from numap.core.usb_device_capability import USBDeviceCapability, DCContainerId


class USBBillboardInterface(USBInterface):
    name = 'BillboardInterface'

    def __init__(self, app, phy):

        super().__init__(
            app=app,
            phy=phy,
            interface_number=0,
            interface_alternate=0,
            interface_class=0,
            interface_subclass=0,
            interface_protocol=0,
            interface_string_index=0,
            endpoints=[],
        )

class DCBillboard(USBDeviceCapability):
    '''Section 3.1.5.2'''

    BILLBOARD_CAPABILITY_TYPE = 0x0d

    def __init__(
        self, app, phy,
        additional_info_idx,
        preferred_alternate_mode,
        vconn_power,
        bm_configured,
        alternate_modes,
    ):
        data = struct.pack('<BBBH', additional_info_idx, len(alternate_modes), preferred_alternate_mode, vconn_power)
        data += bm_configured
        data += struct.pack('<I', 0)
        for mode in alternate_modes:
            data += struct.pack('<HBB', *mode)
        super(DCBillboard, self).__init__(app, phy, self.BILLBOARD_CAPABILITY_TYPE, data)
        self.additional_info_idx = additional_info_idx
        self.preferred_alternate_mode = preferred_alternate_mode
        self.vconn_power = vconn_power
        self.bm_configured = bm_configured
        self.alternate_modes = alternate_modes


class USBBillboardDevice(USBDevice):
    name = 'BillboardDevice'

    def __init__(self, app, phy, vid=0x8312, pid=0x8312, **kwargs):
        usb_class = None
        usb_vendor = None
        interfaces = [
            USBBillboardInterface(app=app, phy=phy)
        ]
        configurations = [
            USBConfiguration(
                app=app,
                phy=phy,
                index=0x1,
                string='Billboard configuration',
                interfaces=interfaces,
                attributes=0xc0,
                max_power=0xfa
            )
        ]
        super(USBBillboardDevice, self).__init__(
            app=app,
            phy=phy,
            device_class=USBClass.Billboard,
            device_subclass=0x0,
            protocol_rel_num=0x0,
            max_packet_size_ep0=0x40,
            vendor_id=vid,
            product_id=pid,
            device_rev=0x0,
            manufacturer_string='numap Inc.',
            product_string='numap Billboard',
            serial_number_string='UMAP2-BILL-0123',
            configurations=configurations,
            descriptors=None,
            usb_class=usb_class,
            usb_vendor=usb_vendor,
        )
        self.usb_spec_version = 0x0210
        self.bos = USBBinaryObjectStore(app, phy, capabilities=[
            DCContainerId(app, phy, container_id=b'UMAP2-BILL-12345'),
            DCBillboard(
                app, phy,
                additional_info_idx=self.get_string_id('https://additional.info/numap'),
                preferred_alternate_mode=0,
                vconn_power=0x8000,
                bm_configured=b'\xff' * 16,
                alternate_modes=[
                    (vid, 0, self.get_string_id('alternate_mode_0'))
                ],
            )
        ])


usb_device = USBBillboardDevice
