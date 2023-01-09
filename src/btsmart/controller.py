# -*- coding: utf-8 -*-
"""
Ths module provides simplified access to the Fischertechnik BT-Smart Controller
using the bleak BLE API.
The module heavily relies on asyncio

@Author: Rainer Neumann
@Date: 2022-12-26

Todo:
    * Test Cross-OS compatibility
    * Reading output values does not yet work (currently only workaround)

"""

import asyncio
from enum import Enum

try:
    from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic, BLEDevice, AdvertisementData
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

class LEDMode(Enum):
    pass


class InputMode(Enum):
    pass


class InputMeasurement:
    pass


class BTSmartController:
    pass


# ----------------- relevant classes start here ------------------------

class LEDMode(Enum):
    """Enumeration of the BTSmart internal LED Colors"""
    BLUE = bytearray(b'\x00')
    ORANGE = bytearray(b'\x01')

    def from_bytes(b: bytes) -> LEDMode:
        """derive the color from a given binary representation (received via BLE)

        Args:
            b (bytes): the bytes received via BLE (attributes read)

        Returns:
            LEDMode: the according color or None in case the bytes do not hold a valid represnetation
        """
        if b == LEDMode.ORANGE.value:
            return LEDMode.ORANGE
        else:
            if b == LEDMode.BLUE.value:
                return LEDMode.BLUE
            else:
                return None

LED_LABEL = {
    LEDMode.ORANGE: "Orange",
    LEDMode.BLUE: "Blue"
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

    class _BLEScanner:
        def __init__(self):
            self._device = None
            self._scanner = None
        
        async def _device_detected(self, device: BLEDevice, adv: AdvertisementData):
            if device.name == 'BT Smart Controller':
                self._device = device

        async def _scan(self):
            self.scanner = BleakScanner(self._device_detected)
            await self.scanner.start()
            count = 0
            while self._device is None and count < 50:
                count = count + 1
                await asyncio.sleep(0.1)
            await self.scanner.stop()
            return self._device

    async def discover(autoconnect: bool = True) -> BTSmartController:
        """Start deicobery of bluetooth devices and try to find a BT-Smart Controller

        Args:
            autoconnect (bool, optional): tells the controller to automatically connect if disconnected before performing any command. Defaults to True.

        Raises:
            Exception: if there is not controller found

        Returns:
            BTSmartController: the found controller
        """
        scanner = BTSmartController._BLEScanner()
        btSmartDevice = await scanner._scan()
        if btSmartDevice is None:
            raise Exception("BT Smart Controller not found")
        else:
            print(btSmartDevice.name, "-", btSmartDevice.address)
            return BTSmartController(btSmartDevice, autoconnect=autoconnect)

    def __init__(self, device, autoconnect: bool = True) -> None:
        """Initializes the controller instance using the detected device.

        Args:
            device (BLEDevice): the device
            autoconnect (bool, optional): should the controller automatically connect to the device. Defaults to True.
        """
        self.client = BleakClient(device, disconnected_callback=self._disconnect_cb)
        self.autoconnect = autoconnect
        self.input_listener = {1: None, 2: None, 3: None, 4: None}
        self.diconnect_listener = None

    def _disconnect_cb(self, client) -> None:
        """method is called, when the client is disconnectd"""
        if self.diconnect_listener is not None:
            self.diconnect_listener()
    
    def on_disconnect(self, callback) -> None:
        """registers the given callback function to be called upon client disconnect.
        
        Args:
            callback (function): the function to be called when the controller is disconnected
        """
        self.diconnect_listener = callback

    async def _handle_input_change(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        """callback that is called after a notifyable characteristic in the BLE Device changed.
        This method simply calls the specific input handler.

        Args:
            characteristic (BleakGATTCharacteristic): the changed characteristic
            data (bytearray): the new data of the characteristic
        """
        value = int.from_bytes(data, 'little', signed=False)
        for num, uuid in BT_SMART_GATT_UUIDs["input"]["characteristics"].items():
            if characteristic.uuid == uuid:
                await self._on_input_value_changed(num, value)

    async def _on_input_value_changed(self, input: int, value: int) -> None:
        """callback that is called whenever a certain input value changes. This method is called by the raw input handler above and
        in turn notifies the registered input listener.

        Args:
            input (int): the input number (1..4)
            value (int): the new value
        """
        callback = self.input_listener[input]
        if callback is not None:
            if asyncio.iscoroutinefunction(callback):
                await callback(input, value)
            else:
                callback(input, value)

    def is_connected(self) -> bool:
        """indicates whether or not the controller is currently connected

        Returns:
            bool: True iff the controller is currently connected to BLE device
        """
        return self.client.is_connected

    async def connect(self) -> bool:
        """connects the controller to the BLE device.

        Raises:
            Exception: if the connection could not be established

        Returns:
            bool: True after the connection has been established
        """
        if not self.is_connected():
            await self.client.connect()
        if self.is_connected():
            for number in range(1, 5):
                measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][number]
                try:
                    await self.client.start_notify(measureUuid, self._handle_input_change)
                except:
                    pass
            # signal a connect ba 'blinking' with the led
            await self.set_led(LEDMode.ORANGE)
            await asyncio.sleep(0.5)
            await self.set_led(LEDMode.BLUE)
            await asyncio.sleep(0.5)
            await self.set_led(LEDMode.ORANGE)
            
            
            for i in range(1, 5):
                await self.set_input_mode(i, InputMode.RESISTANCE)
            
            return True
        else:
            raise Exception("unable to connect")

    async def disconnect(self) -> None:
        """disconnects the controller from the BLE device"""
        if self.is_connected():
            #for number in range(1, 5):
            #    measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][number]
            #    await self.client.stop_notify(measureUuid)
            await self.client.disconnect()

    async def _autoconnect(self) -> None:
        """convenience-method that checks if we should automatically connect to the device (ad-hoc) and optionally connects"""
        if not self.is_connected():
            if self.autoconnect:
                await self.connect()
            else:
                raise Exception("Device not connected")

    async def _read_gatt_char(self, uuid) -> bytes:
        res = await self.client.read_gatt_char(uuid)
        #print("r:", uuid, " -> ", res)
        return res

    async def _write_gatt_char(self, uuid, bytes, response: bool = True):
        #print("w:", uuid, " -> ", bytes)
        await self.client.write_gatt_char(uuid, bytes, response=True)

    async def get_device_information(self) -> dict[str, str]:
        """retrieves device information from the attached BT-Smart Controller

        Returns:
            dict[str, str]: a dictionary containing information for the keys "manufacturer", "model", "hardware", "firmware" and "sysid"
        """
        await self._autoconnect()
        res = dict()
        for key, uuid in BT_SMART_GATT_UUIDs["device_info"]["characteristics"].items():
            try:
                res[key] = await self._read_gatt_char(uuid)
            except:
                pass
        return res

    async def get_battery_level(self) -> int:
        """retrieves the battery level of the device

        Returns:
            int: the battery level
        """
        await self._autoconnect()
        uuid = BT_SMART_GATT_UUIDs["battery"]["characteristics"]["level"]
        m_bts = await self._read_gatt_char(uuid)
        value = int.from_bytes(m_bts, 'little', signed=False)
        return value

    async def set_led(self, led: LEDMode) -> None:
        """choses the LED on the controller

        Args:
            led (LEDMode): the LED to be used
        """
        ledUuid = BT_SMART_GATT_UUIDs["led"]["characteristics"]["color"]
        bts = led.value
        await self._write_gatt_char(ledUuid, bts)

    async def get_led(self) -> LEDMode:
        """get the currently used LED

        Returns:
            LEDMode: the currently used LED
        """
        ledUuid = BT_SMART_GATT_UUIDs["led"]["characteristics"]["color"]
        bts = await self._read_gatt_char(ledUuid)
        led = LEDMode.from_bytes(bts)
        return led

    async def set_input_mode(self, number: int, unit: InputMode) -> None:
        """set the input mode of the given input to either "voltage" or "resitance" """
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][number]
        u_bts = unit.value
        await self._write_gatt_char(unitUuid, u_bts)

    async def get_input_mode(self, number: int) -> InputMode:
        """retrieves the currently set input mode of the given input"""
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][number]
        u_bts = await self._read_gatt_char(unitUuid)
        return InputMode.from_bytes(u_bts)

    async def get_input_value(self, number: int, unit: InputMode = None) -> InputMeasurement:
        """retrieves the current measure on the given input

        Args:
            number (int): th input number
            unit (InputMode, optional): the mode to be used for measurement. Defaults to None.

        Raises:
            Exception: if the input number is incorrect (must be 1..4)

        Returns:
            InputMeasurement: the object containing value and unit
        """
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][number]
        measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][number]
        if unit is not None:
            await self.set_input_mode(number, unit)
        r_unit = await self.get_input_mode(number)
        m_bts = await self._read_gatt_char(measureUuid)
        value = int.from_bytes(m_bts, 'little', signed=False)
        return InputMeasurement(value, r_unit)

    def on_input_change(self, number: int, callback) -> None:
        """registers a listener for the given input. Currently, there is only one listener allowed.
        A callback function might be a normal function or an async function that takes two arguments, the number of the input and the value.
        
        e.g. [async] def callback(input: int, value: int)

        Args:
            number (int): the input number (must be 1..4)
            callback (function): the callback function

        Raises:
            Exception: if the input number is invalid
        """
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        self.input_listener[number] = callback

    async def set_output_value(self, number: int, value: int) -> None:
        """sets the output value of the given pin to the given value

        Args:
            number (int): the output number (1 or 2)
            value (int): the value to be set (must be in the range -100..100)

        Raises:
            Exception: if either output number or the value is invalid 
        """
        if number < 1 or number > 2:
            raise Exception("invalid input number - must be in 1..2")
        if value < int(-100) or value > int(100):
            raise Exception("motor output must be in -100..100")
        char_uuid = BT_SMART_GATT_UUIDs["output"]["characteristics"][number]
        bts = value.to_bytes(1, 'little', signed=True)
        await self._write_gatt_char(char_uuid, bts)

    async def get_output_value(self, number: int) -> int:
        """retrieves the current output value

        Args:
            number (int): the output number (must be 1..2)

        Raises:
            Exception: if the output number is invalid

        Returns:
            int: the value that is currently set for the output
        """
        if number < 1 or number > 2:
            raise Exception("invalid input number - must be in 1..2")
        char_uuid = BT_SMART_GATT_UUIDs["output"]["characteristics"][number]
        bts = await self._read_gatt_char(char_uuid)
        value = int.from_bytes(bts, 'little', signed=True)
        return value
