import asyncio

from enum import Enum
from bleak import BleakScanner, BleakClient, BleakGATTCharacteristic, BLEDevice, AdvertisementData

from .controller import LEDMode, Input, Output, InputMode, INPUT_MODE_UNIT, InputMeasurement, BTSmartController


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
            Output.O1: "8ae8860c-ad7d-11e6-80f5-76304dec7eb7",
            # read,write-without-response,write  Val: bytearray(b'\x00') -- valid range: –100..100
            Output.O2: "8ae88b84-ad7d-11e6-80f5-76304dec7eb7"
            # read,write-without-response,write  Val: bytearray(b'\x00') -- valid range: –100..100
        }
    },
    "input_mode": {
        "uuid": "8ae88d6e-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {  ## 1 byte: 0x0a = voltage, 0x0b = resistance
            Input.I1: "8ae88efe-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            Input.I2: "8ae89084-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            Input.I3: "8ae89200-ad7d-11e6-80f5-76304dec7eb7",  # read,write  Val: bytearray(b'\x0b')
            Input.I4: "8ae89386-ad7d-11e6-80f5-76304dec7eb7"  # read,write  Val: bytearray(b'\x0b')
        }
    },
    "input": {
        "uuid": "8ae8952a-ad7d-11e6-80f5-76304dec7eb7",
        "characteristics": {  ## 2 bytes: value in ohms or volt
            Input.I1: "8ae89a2a-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            Input.I2: "8ae89bec-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            Input.I3: "8ae89dc2-ad7d-11e6-80f5-76304dec7eb7",  # read,notify  Val: bytearray(b'\xff\xff')
            Input.I4: "8ae89f66-ad7d-11e6-80f5-76304dec7eb7"  # read,notify  Val: bytearray(b'\xff\xff')
        }
    }
}


class BTSmartController_BLE(BTSmartController):
    pass

class BTSmartController_BLE(BTSmartController):
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

    async def discover() -> BTSmartController:
        """Start discovery of bluetooth devices and try to find a BT-Smart Controller

        Returns:
            BTSmartController: the found controller or None
        """
        scanner = BTSmartController_BLE._BLEScanner()
        btSmartDevice = await scanner._scan()
        if btSmartDevice is None:
            print("BT Smart Controller not found")
            return None
        else:
            print("found", btSmartDevice.name, "-", btSmartDevice.address)
            return BTSmartController_BLE(btSmartDevice)

    def __init__(self, device) -> None:
        """Initializes the controller instance using the detected device.

        Args:
            device (BLEDevice): the device
        """
        super().__init__()
        self.client = BleakClient(device, disconnected_callback=self._disconnect_cb)

    async def _handle_input_change(self, characteristic: BleakGATTCharacteristic, data: bytearray) -> None:
        """callback that is called after a notifyable characteristic in the BLE Device changed.
        This method simply calls the specific input handler.

        Args:
            characteristic (BleakGATTCharacteristic): the changed characteristic
            data (bytearray): the new data of the characteristic
        """
        value = int.from_bytes(data, 'little', signed=False)
        #print("i changed", BT_SMART_GATT_UUIDs["input"]["characteristics"].items())
        for input, uuid in BT_SMART_GATT_UUIDs["input"]["characteristics"].items():
            #print("checking: ", input, uuid, characteristic.uuid)
            if characteristic.uuid == uuid:
                #print("found: ", input)
                await self._on_input_value_changed(input, value)

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
            await self.reset()
            for input in Input.all():
                measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][input]
                try:
                    await self.client.start_notify(measureUuid, self._handle_input_change)
                except:
                    pass
            return True
        else:
            raise Exception("unable to connect")

    async def disconnect(self) -> None:
        """disconnects the controller from the BLE device"""
        if self.is_connected():
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

    async def set_input_mode(self, input: Input, unit: InputMode) -> None:
        """set the input mode of the given input to either "voltage" or "resitance" """
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][input]
        u_val: int = unit.value
        u_bts = u_val.to_bytes(1, 'little')
        await self._write_gatt_char(unitUuid, u_bts)

    async def get_input_mode(self, input: Input) -> InputMode:
        """retrieves the currently set input mode of the given input"""
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][input]
        u_bts = await self._read_gatt_char(unitUuid)
        return InputMode.from_bytes(u_bts)

    async def get_input_value(self, input: Input, mode: InputMode = None) -> InputMeasurement:
        """retrieves the current measure on the given input

        Args:
            input (Input): the input to be read
            mode (InputMode, optional): the mode to be used for measurement. Defaults to None.

        Returns:
            InputMeasurement: the object containing value and unit
        """
        unitUuid = BT_SMART_GATT_UUIDs["input_mode"]["characteristics"][input]
        measureUuid = BT_SMART_GATT_UUIDs["input"]["characteristics"][input]
        if mode is not None:
            await self.set_input_mode(input, mode)
        r_unit = await self.get_input_mode(input)
        m_bts = await self._read_gatt_char(measureUuid)
        value = int.from_bytes(m_bts, 'little', signed=False)
        return InputMeasurement(value, r_unit)

    async def set_output_value(self, output: Output, value: int) -> None:
        """sets the output value of the given pin to the given value

        Args:
            output (Output): the output (O1 or O2)
            value (int): the value to be set (must be in the range -100..100)

        Raises:
            Exception: if the value is invalid 
        """
        if value < int(-100) or value > int(100):
            raise Exception("output must be in -100..100")
        char_uuid = BT_SMART_GATT_UUIDs["output"]["characteristics"][output]
        bts = value.to_bytes(1, 'little', signed=True)
        await self._write_gatt_char(char_uuid, bts)

    async def get_output_value(self, output: Output) -> int:
        """retrieves the current output value

        Args:
            output (Output): the output number (must be O1 or O2)

        Returns:
            int: the value that is currently set for the output
        """
        char_uuid = BT_SMART_GATT_UUIDs["output"]["characteristics"][output]
        bts = await self._read_gatt_char(char_uuid)
        value = int.from_bytes(bts, 'little', signed=True)
        return value
