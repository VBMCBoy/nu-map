'''
Implement a Communication Device Class (CDC) Network Control Model (NCM)
device.
The specification for this device may be found in NCM10-20101124-track.pdf
'''
import struct
from numap.core.usb_interface import USBInterface
from numap.core.usb_class import USBClass
from numap.core.usb_endpoint import USBEndpoint
from numap.dev.cdc import USBCDCDevice
from numap.dev.cdc import CommunicationClassSubclassCodes
from numap.dev.cdc import CommunicationClassProtocolCodes
from numap.dev.cdc import DataInterfaceClassProtocolCodes
from numap.dev.cdc import FunctionalDescriptor as FD


class USBCdcNcmDevice(USBCDCDevice):

    name = 'CDC NCM Device'

    bControlSubclass = CommunicationClassSubclassCodes.NetworkControlModel
    # TODO check both 0x00 (NoClassSpecificProtocolRequired) and 0xfe (ExternalProtocol)?
    # TODO this requires implementing two devices...?
    bControlProtocol = CommunicationClassProtocolCodes.NoClassSpecificProtocolRequired
    bDataProtocol = DataInterfaceClassProtocolCodes.NetworkTransferBlock

    def __init__(self, app, phy, vid=0x2548, pid=0x1001, rev=0x0010, cs_interfaces=None, cdc_cls=None, bmCapabilities=0x01, **kwargs):
        if cdc_cls is None:
            cdc_cls = self.get_default_class(app, phy)
        cs_interfaces = [
            # Header Functional Descriptor
            FD(app, phy, FD.Header, b'\x01\x01'),
            # Call Management Functional Descriptor
            FD(app, phy, FD.NCM, struct.pack('HB',
                                             # 2 bytes int (little-endian) bcdNcmVersion
                                             0x0100,
                                             # 1 byte bitmap bmNetworkCapabilities
                                             0xff)),
            FD(app, phy, FD.EN, struct.pack('<BIHHB',
                                            # 1 byte int iMACAddress is technically a pointer,
                                            # but I don't know how to implement that here...
                                            1,

                                            # 4 bytes bitmap bmEthernetStatistics
                                            # (all set means all statistics are supported)
                                            0xffffffff,

                                            # 2 bytes int wMaxSegmentSize typically 1514
                                            1514,

                                            # 2 bytes bitmap wNumberMCFilters
                                            0xffff,

                                            # 1 byte int bNumberPowerFilters
                                            0
                                            )),
            FD(app, phy, FD.UN, struct.pack(b'BB', USBCDCDevice.bControlInterface, USBCDCDevice.bDataInterface)),
        ]
        interfaces = [
            USBInterface(
                app=app, phy=phy,
                interface_number=self.bDataInterface,
                interface_alternate=0,
                interface_class=USBClass.CDCData,
                interface_subclass=self.bDataSubclass,
                interface_protocol=self.bDataProtocol,
                interface_string_index=0,
                endpoints=[
                    USBEndpoint(
                        app=app,
                        phy=phy,
                        number=0x1,
                        direction=USBEndpoint.direction_out,
                        transfer_type=USBEndpoint.transfer_type_bulk,
                        sync_type=USBEndpoint.sync_type_none,
                        usage_type=USBEndpoint.usage_type_data,
                        max_packet_size=0x40,
                        interval=0x00,
                        handler=self.handle_ep1_data_available
                    ),
                    USBEndpoint(
                        app=app,
                        phy=phy,
                        number=0x2,
                        direction=USBEndpoint.direction_in,
                        transfer_type=USBEndpoint.transfer_type_bulk,
                        sync_type=USBEndpoint.sync_type_none,
                        usage_type=USBEndpoint.usage_type_data,
                        max_packet_size=0x40,
                        interval=0x00,
                        handler=self.handle_ep2_buffer_available
                    )
                ],
                usb_class=cdc_cls
            )
        ]
        super(USBCdcNcmDevice, self).__init__(
            app, phy,
            vid=vid, pid=pid, rev=rev,
            interfaces=interfaces, cs_interfaces=cs_interfaces, cdc_cls=cdc_cls,
            bmCapabilities=0x03, **kwargs
        )
        self.receive_buffer = b''

    def handle_ep1_data_available(self, data):
        '''
        print the AT commands only upon new line
        '''
        self.receive_buffer += data
        if b'\r' in self.receive_buffer:
            lines = self.receive_buffer.split(b'\r')
            self.receive_buffer = lines[-1]
            for l in lines[:-1]:
                self.info('received line: %s' % l)

    def handle_ep2_buffer_available(self):
        # send ARP
        self.debug('in handle ep2 buffer available')
        self.send_on_endpoint(
            2,
            b'\xff\xff\xff\xff\xff\xff\xaa\xbb\xcc\xdd\xee\xff\x08\x06\x00\x01\x08\x00\x06\x04\x00\x01\x60\x03\x08\xaa\xaa\xaa\xc0\xa8\x00\x65\x00\x00\x00\x00\x00\x00\xc0\xa8\x01\x00'
        )


usb_device = USBCdcNcmDevice
