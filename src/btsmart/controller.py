# -*- coding: utf-8 -*-
"""
Ths module provides simplified access to the Fischertechnik BT-Smart Controller
using the bleak BLE API.
The module heavily relies on asyncio

@Author: Rainer Neumann
@Date: 2022-12-26

Todo:
    * Make discovery more convenient
    * Test Cross-OS compatibility

"""

import asyncio
from enum import Enum

try:
    from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic
except ModuleNotFoundError as e:
    print("Error loading bleak module:", e);
    print("You may install it via 'pip3 install bleak' ...");
    exit(-1);

BT_SMART_GATT_UUIDs = {
    "device_info": {
        "uuid": "0000180a-0000-1000-8000-00805f9b34fb",
        "characteristics": {
            "manufacturer": "00002a29-0000-1000-8000-00805f9b34fb",  # String read  Val: bytearray(b'fischertechnik')
            "model": "00002a24-0000-1000-8000-00805f9b34fb",  # String read  Val: bytearray(b'161944')
            "hardware": "00002a27-0000-1000-8000-00805f9b34fb",  # String read  Val: bytearray(b'1\x00')
            "firmware": "00002a26-0000-1000-8000-00805f9b34fb",  # String read  Val: bytearray(b'1.63\x00\x00\x00\x00')
            "sysid": "00002a23-0000-1000-8000-00805f9b34fb"
            # bytes  read  Val: bytearray(b'\x00\x00\x00\x00\x00\xf8E\x10')
        }
    },
    "battery": {
        "uuid": "0000180f-0000-1000-8000-00805f9b34fb",
        "characteristics": {
            "level": "00002a19-0000-1000-8000-00805f9b34fb"  # read,notify  Val: bytearray(b'd')
        }
    },
    "led": {
        "uuid": "8ae87702-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {
            "color": "8ae87e32-ad7d-11e6-80f5-76304dec7eb7"
            # read,write-without-response,write  Val: bytearray(b'\x00') -- 00 = blue, 01 = orange
        }
    },
    "output": {
        "uuid": "8ae883b4-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {
            1: "8ae8860c-ad7d-11e6-80f5-76304dec7eb7",
            # read,write-without-response,write  Val: bytearray(b'\x00') -- valid range: –100..100
            2: "8ae88b84-ad7d-11e6-80f5-76304dec7eb7"
            # read,write-without-response,write  Val: bytearray(b'\x00') -- valid range: –100..100
        }
    },
    "input_mode": {
        "uuid": "8ae88d6e-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {  ## 1 byte: 0x0a = voltage, 0x0b = resistance
            1: "8ae88efe-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            2: "8ae89084-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            3: "8ae89200-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            4: "8ae89386-ad7d-11e6-80f5-76304dec7eb7"  # read,write  Val: bytearray(b'\x0b')
        }
    },
    "input": {
        "uuid": "8ae8952a-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {  ## 2 bytes: value in ohms or volt
            1: "8ae89a2a-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            2: "8ae89bec-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            3: "8ae89dc2-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            4: "8ae89f66-ad7d-11e6-80f5-76304dec7eb7"  # read,notify  Val: bytearray(b'\xff\xff')
        }
    }
}


# ----------------- some forward declarations ----------------

class LED_Mode(Enum):
    pass


class InputMode(Enum):
    pass


class InputMeasurement:
    pass


class BTSmartController:
    pass


# ----------------- relevant classes start here ------------------------

class LED_Mode(Enum):
    """Enumeration of the BTSmart internal LED Colors"""
    ORANGE = bytearray(b'\x00')
    BLUE = bytearray(b'\x01')

    def from_bytes(b: bytes) -> LED_Mode:
        """derive the color from a given binary representation (received via BLE)

        Args:
            b (bytes): the bytes received via BLE (attributes read)

        Returns:
            LED_Mode: the according color or None in case the bytes do not hold a valid represnetation
        """
        if b == LED_Mode.ORANGE.value:
            return LED_Mode.ORANGE
        else:
            if b == LED_Mode.BLUE.value:
                return LED_Mode.BLUE
            else:
                return None

LED_Label = {
    LED_Mode.ORANGE: "Orange",
    LED_Mode.BLUE: "Blue"
}


class InputMode(Enum):
    """Enumeration of the input measurement modes"""
    VOLTAGE = b'\x0a'
    RESISTANCE = b'\x0b'

    def from_bytes(b: bytes) -> InputMode:
        """derive the input mode from a given binary representation (received via BLE)

        Args:
            b (bytes): the bytes received via BLE (attributes read)

        Returns:
            InputMode: the according mode or None in case the bytes do not hold a valid represnetation
        """
        if b == InputMode.VOLTAGE.value:
            return InputMode.VOLTAGE
        else:
            if b == InputMode.RESISTANCE.value:
                return InputMode.RESISTANCE
            else:
                return None

INPUT_MODE_LABEL = {
    InputMode.VOLTAGE: "Volt",
    InputMode.RESISTANCE: "Ohm"
}

class InputMeasurement:
    """Simple object containing a measurement value and unit """

    def __init__(self, value: int, unit: InputMode) -> InputMeasurement:
        """creates a measurement with the given value and unit

        Args:
            value (int): the measured value
            unit (InputMode): the unit of measurement

        Returns:
            InputMeasurement: the compound object
        """
        self.value = value
        self.unit = unit

    def __str__(self):
        """simple format using readable unit identifiers"""
        return str(self.value) + " " + INPUT_MODE_LABEL[self.unit]


class BTSmartController:
    """This class represents a BTSmart-Controller, connected via BLE"""

    async def discover(autoconnect: bool = True) -> BTSmartController:
        """Start deicobery of bluetooth devices and try to find a BT-Smart Controller

        Args:
            autoconnect (bool, optional): tells the controller to automatically connect if disconnected before performing any command. Defaults to True.

        Raises:
            Exception: if there is not controller found

        Returns:
            BTSmartController: the found controller
        """
        devices = await BleakScanner.discover(return_adv=True)
        btSmartDevice = None
        for d, a in devices.values():
            if (d.name == 'BT Smart Controller'):
                btSmartDevice = d
        if btSmartDevice is None:
            raise Exception("BT Smart Controller not found")
        else:
            print(btSmartDevice.name, "-", btSmartDevice.address)
            return BTSmartController(btSmartDevice, autoconnect=autoconnect)

    async def find(address, autoconnect: bool = True) -> BTSmartController:
        btSmartDevice = await BleakScanner.find_device_by_address(address)
        if btSmartDevice is None:
            raise Exception("BT Smart Controller not found")
        else:
            print(btSmartDevice.name, "-", btSmartDevice.address)
            return BTSmartController(btSmartDevice, autoconnect=autoconnect)

    def __init__(self, device, autoconnect: bool = True) -> None:
        self.client = BleakClient(device, disconnected_callback=self.on_disconnect)
        self.autoconnect = autoconnect
        self.input_listener = {1: None, 2: None, 3: None, 4: None}

    def on_disconnect(self, client) -> None:
        pass

    async def _handle_input_change(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        value = int.from_bytes(data, 'little', signed=False)
        for num, uuid in BT_SMART_GATT_UUIDs["input"]["characteristics"].items():
            if characteristic.uuid == uuid:
                await self._on_input_value_changed(num, value)

    async def _on_input_value_changed(self, input: int, value: int) -> None:
        callback = self.input_listener[input]
        if callback is not None:
            if asyncio.iscoroutinefunction(callback):
                await callback(input, value)
            else:
                callback(input, value)

    def is_connected(self) -> bool:
        return self.client.is_connected

    async def connect(self) -> bool:
        if not self.is_connected():
            await self.client.connect()
        if self.is_connected():
            for number in range(1, 5):
                measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][number]
                await self.client.start_notify(measureUuid, self._handle_input_change)
            return True
        else:
            raise Exception("unable to connect")

    async def disconnect(self) -> None:
        if self.is_connected():
            await self.client.disconnect()

    async def _autoconnect(self) -> None:
        if not self.is_connected():
            if self.autoconnect:
                await self.connect()
            else:
                raise Exception("Device not connected")

    async def get_device_information(self) -> dict[str, str]:
        await self._autoconnect()
        res = dict()
        for key, uuid in BT_SMART_GATT_UUIDs["device_info"]["characteristics"].items():
            try:
                res[key] = await self.client.read_gatt_char(uuid)
            except:
                pass
        return res

    async def set_led(self, led: LED_Mode) -> None:
        ledUuid = BT_SMART_GATT_UUIDs["led"]["characteristics"]["color"]
        bts = led.value
        await self.client.write_gatt_char(ledUuid, bts)

    async def get_led(self) -> LED_Mode:
        ledUuid = BT_SMART_GATT_UUIDs["led"]["characteristics"]["color"]
        bts = await self.client.read_gatt_char(ledUuid)
        print(">>>led: ", bts)
        led = LED_Mode.from_bytes(bts)
        return led

    async def set_input_mode(self, number: int, unit: InputMode) -> None:
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][number]
        u_bts = unit.value
        await self.client.write_gatt_char(unitUuid, u_bts)

    async def get_input(self, number: int, unit: InputMode = None) -> InputMeasurement:
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][number]
        measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][number]
        if unit is not None:
            u_bts = unit.value
            await self.client.write_gatt_char(unitUuid, u_bts)
        else:
            u_bts = await self.client.read_gatt_char(unitUuid)
            unit = InputMode.from_bytes(u_bts)
        m_bts = await self.client.read_gatt_char(measureUuid)
        value = int.from_bytes(m_bts, 'little', signed=False)
        # print("chars:", m_bts, "->", value)
        return InputMeasurement(value, unit)

    def on_input_change(self, number: int, callback) -> None:
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        self.input_listener[number] = callback

    async def set_output_value(self, number: int, value: int) -> None:
        if number < 1 or number > 2:
            raise Exception("invalid input number - must be in 1..2")
        if value < int(-100) or value > int(100):
            raise Exception("motor output must be in -100..100")
        bts = value.to_bytes(2, 'little', signed=True)
        await self.client.write_gatt_char(BT_SMART_GATT_UUIDs["output"]["characteristics"][number], bts)

    async def get_output_value(self, number: int) -> None:
        if number < 1 or number > 2:
            raise Exception("invalid input number - must be in 1..2")
        bts = await self.client.read_gatt_char(BT_SMART_GATT_UUIDs["output"]["characteristics"][number])
        value = int.from_bytes(bts, 'little', signed=False)
        return value
