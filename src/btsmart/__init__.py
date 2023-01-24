"""This package contains control and convenience-classes for the Fischertechnik BT-Smart Controller Environment."""

__author__ = """Rainer Neumann"""
__email__ = "rainer.neumann@h-ka.de"

import asyncio

from .controller import BTSmartController, LEDMode, LED_LABEL, Input, InputMode, INPUT_MODE_LABEL, InputMeasurement, Output
from .parts import ElectronicsPart, InputPart, OutputPart, Button, LightBarrier, Dimmer, MotorXS

from .backend_ble import BTSmartController_BLE
from .backend_usb import BTSmartController_USB

async def discover_controller(viaUSB: bool = True, viaBLE: bool = True) -> BTSmartController:
    """Tries to discover an attached BTSmartController either via USB or via BLE

    Args:
        viaUSB (bool, optional): Should USB-Lookup be performed. Defaults to True.
        viaBLE (bool, optional): Should BLE-Lookup be performed. Defaults to True.

    Returns:
        BTSmartController: the found controller instance or None
    """
    print("searching for BT-Smart Controller...")
    ctrl: BTSmartController = None
    if viaUSB:
        ctrl = await BTSmartController_USB.discover()
        #print ("USB:", ctrl)
    if (ctrl is None) and viaBLE:
        ctrl = await BTSmartController_BLE.discover()
        #print ("BLE:", ctrl)
    if ctrl is not None:
        print("found controller", type(ctrl))
        await ctrl.connect()
    else:
        print("No BT-Smart-Controller detected!")
    return ctrl