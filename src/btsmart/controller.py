"""
Ths module provides simplified access to the Fischertechnik BT-Smart Controller
using the bleak BLE API.
The module heavily relies on asyncio

@Author: Rainer Neumann
@Date: 2022-12-26

Todo:
    * Reading output values does not yet work (currently only workaround)
    * make BTController a singleton

"""
import asyncio

from enum import Enum


class LEDMode(Enum):
    pass

class InputMode(Enum):
    pass

class InputMeasurement:
    pass


class LEDMode(Enum):
    """Enumeration of the BTSmart internal LED Colors"""
    BLUE = b'\x00'
    YELLOW = b'\x01'
    GREEN = b'\x02'

    def from_bytes(b: bytes) -> LEDMode:
        """derive the color from a given binary representation (received via BLE)

        Args:
            b (bytes): the bytes received via BLE (attributes read)

        Returns:
            LEDMode: the according color or None in case the bytes do not hold a valid represnetation
        """
        if b[0] == LEDMode.BLUE.value:
            return LEDMode.BLUE
        else:
            if b[0] == LEDMode.YELLOW.value:
                return LEDMode.YELLOW
            else:
                if b[0] == LEDMode.GREEN.value:
                    return LEDMode.GREEN
                else:
                    return None

LED_LABEL = {
    LEDMode.BLUE: "Blue",
    LEDMode.YELLOW: "Yellow",
    LEDMode.GREEN: "Green"
}

class Input(Enum):
    """enumeration of the inputs - API-Calls should use these elements rather than the 'raw' values"""
    I1 = 0
    I2 = 1
    I3 = 2
    I4 = 3

    def all() -> list:
        """returns the list of the inputs for use in loops"""
        return [Input.I1, Input.I2, Input.I3, Input.I4]

class Output(Enum):
    """enumeration of the outputs - API-Calls should use these elements rather than the 'raw' values"""
    O1 = 0
    O2 = 1

    def all() -> list:
        """returns the list of the outputs for use in loops"""
        return [Output.O1, Output.O2]

class InputMode(Enum):
    """Enumeration of the input measurement modes"""
    
    VOLTAGE = 10
    """represents voltage measurement at a specific input"""
    
    RESISTANCE = 11
    """represents resistance measurement at a specific iput"""

    def from_bytes(b: bytes) -> InputMode:
        """derive the input mode from a given binary representation (received via BLE)

        Args:
            b (bytes): the bytes received via BLE (attributes read)

        Returns:
            InputMode: the according mode or None in case the bytes do not hold a valid represnetation
        """
        if b[0] == InputMode.VOLTAGE.value:
            return InputMode.VOLTAGE
        else:
            if b[0] == InputMode.RESISTANCE.value:
                return InputMode.RESISTANCE
            else:
                print("unknown input mode", b[0], "  V", InputMode.VOLTAGE.value, " R", InputMode.RESISTANCE.value)
                return None

INPUT_MODE_LABEL = {
    InputMode.VOLTAGE: "Voltage",
    InputMode.RESISTANCE: "Resistance"
}

INPUT_MODE_UNIT = {
    InputMode.VOLTAGE: "mV",
    InputMode.RESISTANCE: u'\u2126'
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
        return str(self.value) + " " + INPUT_MODE_UNIT[self.unit]



class BTSmartController:
    """Abstract class that represents a BTSmart Controller."""

    def __init__(self) -> None:
        self.input_listener = {Input.I1: None, Input.I2: None, Input.I3: None, Input.I4: None}
        self.diconnect_listener = None

    def _disconnect_cb(self, client) -> None:
        """method is called, when the client is disconnectd"""
        if self.diconnect_listener is not None:
            try:
                self.diconnect_listener()
            except:
                pass
    
    def on_disconnect(self, callback) -> None:
        """registers the given callback function to be called upon client disconnect.
        
        Args:
            callback (function): the function to be called when the controller is disconnected
        """
        self.diconnect_listener = callback

    async def _on_input_value_changed(self, input: Input, value: int) -> None:
        """callback that is called whenever a certain input value changes. This method is called by the raw input handler above and
        in turn notifies the registered input listener.

        Args:
            input (Input): the input (I1..I4)
            value (int): the new value
        """
        callback = self.input_listener[input]
        #print("input changed", input, value, callback)
        if callback is not None:
            try:
                if asyncio.iscoroutinefunction(callback):
                    await callback(input, value)
                else:
                    callback(input, value)
            except Exception as ex:
                print("error in callback:", ex)

    def is_connected(self) -> bool:
        """indicates whether or not the controller is currently connected.
        
        This method must be implemented in derived classes

        Returns:
            bool: True iff the controller is connected
        """
        raise NotImplemented

    async def reset(self):
        """Resets the controller to a defined start setting. This method is called after the controller is connected."""
        await self.set_led(LEDMode.YELLOW)
        await asyncio.sleep(0.2)
        await self.set_led(LEDMode.BLUE)
        await asyncio.sleep(0.2)
        await self.set_led(LEDMode.GREEN)
        for i in Input.all():
            await self.set_input_mode(i, InputMode.RESISTANCE)

    async def connect(self) -> bool:
        """Connects the logical controller to the device using the according backend.

        This method must be implemented in derived classes

        Returns:
            bool: True iff the controller has been connected
        """
        raise NotImplemented
            
    async def disconnect(self) -> None:
        """Disconnevts the controller instance from tha according device

        This method must be implemented in derived classes
        """
        raise NotImplemented

    async def get_device_information(self) -> dict[str, str]:
        """retrieves information about hthe underlying physical device

        This method must be implemented in derived classes

        Returns:
            dict[str, str]: descriptive information about the controller
        """
        raise NotImplemented

    async def get_battery_level(self) -> int:
        """retrieves the battery level of the device

        This method must be implemented in derived classes

        Returns:
            int: the battery level
        """
        raise NotImplemented

    async def set_led(self, led: LEDMode) -> None:
        """choses the LED on the controller

        Args:
            led (LEDMode): the LED to be used
        """
        raise NotImplemented

    async def get_led(self) -> LEDMode:
        """get the currently used LED

        Returns:
            LEDMode: the currently used LED
        """
        raise NotImplemented

    async def set_input_mode(self, input: Input, mode: InputMode) -> None:
        """set the input mode of the given input to either "voltage" or "resitance" """
        raise NotImplemented

    async def get_input_mode(self, input: Input) -> InputMode:
        """retrieves the currently set input mode of the given input"""
        raise NotImplemented

    async def get_input_value(self, input: Input, mode: InputMode = None) -> InputMeasurement:
        """retrieves the current measure on the given input

        Args:
            input (Input): the input I1..I4
            unit (InputMode, optional): the mode to be used for measurement. Defaults to None.

        Returns:
            InputMeasurement: the object containing value and unit
        """
        raise NotImplemented

    def on_input_change(self, input: Input, callback) -> None:
        """registers a listener for the given input. Currently, there is only one listener allowed.
        A callback function might be a normal function or an async function that takes two arguments, the number of the input and the value.
        
        e.g. [async] def callback(input: int, value: int)

        Args:
            input(Input): the input to attach the callback to
            callback (function): the callback function

        Raises:
            Exception: if the input number is invalid
        """
        self.input_listener[input] = callback

    async def set_output_value(self, output: Output, value: int) -> None:
        """sets the output value of the given pin to the given value

        Args:
            output (Output): the output (O1 or O2)
            value (int): the value to be set (must be in the range -100..100)

        Raises:
            Exception: if the value is invalid 
        """
        raise NotImplemented

    async def get_output_value(self, output: Output) -> int:
        """retrieves the current output value

        Args:
            output (Output): the output

        Returns:
            int: the value that is currently set for the output
        """
        raise NotImplemented
