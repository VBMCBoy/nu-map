from enum import IntEnum

from numap.dev.audio import USBAudioDevice, USBAudioClass
from numap.dev.keyboard import USBKeyboardDevice, USBKeyboardClass
from numap.dev.mass_storage import USBMassStorageDevice, USBMassStorageClass
from numap.dev.printer import USBPrinterDevice, USBPrinterClass
from numap.dev.cdc_acm import USBCdcAcmDevice
from numap.dev.cdc import USBCDCClass
from numap.dev.rndis import USBRndisDevice, USBRndisClass


DEVICES = [
    ('keyboard', USBKeyboardDevice, USBKeyboardClass),
    ('audio', USBAudioDevice, USBAudioClass),
    ('mass_storage', USBMassStorageDevice, USBMassStorageClass),
    ('printer', USBPrinterDevice, USBPrinterClass),
    ('cdc_acm', USBCdcAcmDevice, USBCDCClass),
    ('rndis', USBRndisDevice, USBRndisClass)
]

class OS(IntEnum):
    UNKNOWN = 0
    WINDOWS = 1
    LINUX = 2
    MACOS = 3
    IOS = 4
# todo: currently only Windows and Linux are differentiated, expand this to other OSs?
# if necessary these could additionally return a weight if the classification is sometimes false
# syntax: (Tuple[device name] (as in DEVICES) or 'ANY', description):
#       lambda reqs, conf_reqs -> [OS.*]; reqs is all requests, conf_reqs is all up to (excluding) configuration
#       return all OSs that may fit
# only use negated OSs if you can be sure that this is the case...
FINGERPRINTS = {
    # HID, CDC-ACM: Windows does three "Get Configuration Descriptor" requests, while other OSs do 2
    (('keyboard', 'cdc_acm', 'rndis'), '>3x Get Configuration Descriptor'):
        lambda reqs, conf_reqs:
        [OS.WINDOWS] if len(
            [cr for cr in conf_reqs if (cr.get_request_number_string() == 'GET_DESCRIPTOR') and (
                    cr.get_descriptor_number_string() == 'CONFIGURATION')]) >= 3 else [OS.LINUX],

    # HID: Windows ignores String index 0x01, not sure what this exactly is, String index may vary... (Manufacturer?)
    (('keyboard',), 'Request String 0x01 (Manufacturer String???)'):
        lambda reqs, conf_reqs:
        [OS.LINUX] if [r for r in reqs if
                       (r.get_request_number_string() == 'GET_DESCRIPTOR') and
                       (r.get_descriptor_number_string() == 'STRING') and
                       (r.value & 0xff == 0x01)]
        else [OS.WINDOWS],

    # ALL?: Windows *sometimes* requests Microsoft OS descriptors
    # apparently this is only the case when the device hasn't been attached to the host before...
    # https://learn.microsoft.com/en-us/windows-hardware/drivers/usbcon/microsoft-defined-usb-descriptors
    ('ANY', 'Request Microsoft OS Descriptor'):
        lambda reqs, conf_reqs:
        [OS.WINDOWS] if [r for r in reqs if
                         (r.get_request_number_string() == 'GET_DESCRIPTOR') and
                         (r.value == 0x03ee)]
        else [OS.UNKNOWN],

    # TODO Linux uses Read Capacity and Test Unit Ready, while Windows does not
#   (('mass_storage',), 'Queries Capacity'):
#       lambda reqs, conf_reqs:
#       [OS.LINUX],

    # Linux sets Audio current (1) and Resolution (4) often, Windows does not
    # TODO test this for other OSs
    (('audio',), 'Set Audio Properties'):
        lambda reqs, conf_reqs:
        [OS.LINUX] if [r for r in reqs if
                       (r.get_request_number_string() == 'class request 4') or
                       (r.get_request_number_string() == 'class request 1')]
        else [OS.WINDOWS],

    # Windows gets the configuration descriptor even after the printer has been configured
    # TODO maybe also true for other devices?
    (('printer',), 'Get Configuration Descriptor after Configuration'):
        lambda reqs, conf_reqs:
        [OS.WINDOWS] if len([r for r in reqs[len(conf_reqs)-1:] if
                             (r.get_request_number_string() == 'GET_DESCRIPTOR') and
                             (r.get_descriptor_number_string() == 'CONFIGURATION')]) > 1
        else [OS.LINUX],

    # when using a CDC ACM or RNDIS device, Windows runs more and additional class requests in comparison to Linux
    # Linux does not run class requests RNDIS devices (not supported?)
    (('cdc_acm', 'rndis'), 'Additional Class Requests'):
        lambda reqs, conf_reqs:
        [OS.WINDOWS] if len([r for r in reqs if
                             r.get_request_number_string().startswith('class request ') and
                             r.get_request_number_string().endswith(('32', '33', '34'))]) > 1
        else [OS.LINUX],
}
