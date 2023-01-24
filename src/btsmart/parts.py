# -*- coding: utf-8 -*-
"""
Ths module provides convenience classes to easily represent built scenarios and
according logic.

@Author: Rainer Neumann
@Date: 2022-12-26

Todo:
    * Add more convenience functionality - more parts
    * need an ideo of how to automatically set the right iput mode for a part (protocol problem with attach and connect)
    * needs more documentation

"""

import asyncio
from .controller import BTSmartController, Input, InputMode, Output

class ElectronicsPart:
    """Simple base class for all representatives of electronical parts that might be attached to a controller.
       These classes are just for convenience.
    """
    
    def __init__(self) -> None:
        self.controller: BTSmartController = None

    def is_attached(self) -> bool:
        """tells if th epart is already attached to the controller or not"""
        return self.controller is not None


class InputPart(ElectronicsPart):
    """Represents input parts, i.e. parts attached to the input-connectors."""
    
    def __init__(self) -> None:
        super().__init__()
        self.inputValueChanged = None
        self.lastValue: int = None

    def attach(self, ctrl: BTSmartController, input: Input) -> None:
        """attaches the part to the given controller and the specified input port

        Args:
            ctrl (BTSmartController): the controller to attach the part to
            input (Input): the input (I1..I4)

        Raises:
            Exception: if no controller is specified
        """
        if ctrl is None:
            raise Exception("cannot attach InputPart to 'None'")
        ctrl.on_input_change(input, self._on_input_change_)
        self.controller = ctrl

    async def _on_input_change_(self, input, value) -> None:
        """this method is called, when the input value changes on the controller.
        This method sould be overrridden in subclasses - it does nothing here.
        Args:
            num (_type_): the input (I1..I4)
            value (_type_): the new value
        """
        pass


class OutputPart(ElectronicsPart):
    """Represents output parts, i.e. parts attached to the output-connectors."""
    
    def __init__(self) -> None:
        super().__init__()
        self.lastValue: int = None
        self.outpin = Output.O1

    def attach(self, ctrl: BTSmartController, output: Output) -> None:
        """attaches the part to the given controller and the specified output port

        Args:
            ctrl (BTSmartController): the controller to attach the part to
            outpt (Output): the output port (O1..O2)

        Raises:
            Exception: if no controller is specified
        """
        if ctrl is None:
            raise Exception("cannot attach Part to 'None'")
        self.outpin = output
        self.controller = ctrl


class Switch(InputPart):
    """Representation of a electrical switch, i.e. an elemnt that is either open or closed. Sitches might be buttons or light barriers"""
    
    def __init__(self) -> None:
        super().__init__()
        self.threshold = 200

    def is_open(self) -> bool:
        """determine if the switch is currently open

        Returns:
            bool: if the switch is currently open
        """
        if self.lastValue is not None:
            return self.lastValue.value < self.threshold
        else:
            return False


class Button(Switch):
    """A special variant of the switch that can be pressed or released.
    In later versions there might also be such things as double-click, long-click or whatever..."""
    
    def __init__(self) -> None:
        super().__init__()
        self._pressed = None  # callback function without parameters
        self._released = None  # callback function without parameters

    def on_press(self, callback) -> None:
        """register a function to be called when the button is pressed.
        A pressed button is detected by low resistance.

        Args:
            callback (function): the (parameterless) function to be called
        """
        self._pressed = callback

    def on_release(self, callback) -> None:
        """register a function to be called when the button is released.
        A pressed button is detected by high resistance.

        Args:
            callback (function): the (parameterless) function to be called
        """
        self._released = callback

    def is_pressed(self) -> bool:
        """determine if the button is currently pressed

        Returns:
            bool: if the button is pressed
        """
        if self.lastValue is not None:
            return self.lastValue.value < self.threshold
        else:
            return False

    async def _on_input_change_(self, input: Input, value: int) -> None:
        oldval = self.lastValue
        self.lastValue = value
        if value < self.threshold:
            if oldval is None or oldval > self.threshold:
                if self._pressed is not None:
                    if asyncio.iscoroutinefunction(self._pressed):
                        await self._pressed()
                    else:
                        self._pressed()
        else:
            if oldval is not None and oldval <= self.threshold:
                if self._released is not None:
                    if asyncio.iscoroutinefunction(self._released):
                        await self._released()
                    else:
                        self._released()


class LightBarrier(Switch):
    def __init__(self) -> None:
        super().__init__()
        self._opened = None
        self._interrupted = None

    def on_interrupt(self, callback) -> None:
        """register a function to be called when the light barrier is interrupted.
        This is detected by high resistance.

        Args:
            callback (function): the (parameterless) function to be called
        """
        self._interrupted = callback

    def on_release(self, callback) -> None:
        """register a function to be called when the light barrier is opened again.
        This is detected by low resistance.

        Args:
            callback (function): the (parameterless) function to be called
        """
        self._opened = callback


    async def _on_input_change_(self, input: Input, value: int) -> None:
        oldval = self.lastValue
        self.lastValue = value
        if value < self.threshold:
            if oldval is None or oldval > self.threshold:
                if self._opened is not None:
                    if asyncio.iscoroutinefunction(self._opened):
                        await self._opened()
                    else:
                        self._opened()
        else:
            if oldval is not None and oldval <= self.threshold:
                if self._interrupted is not None:
                    if asyncio.iscoroutinefunction(self._interrupted):
                        await self._interrupted()
                    else:
                        self._interrupted()


class Dimmer(OutputPart):
    """represents a dimmable part (e.g. a simple light) attached to an output port"""
    
    def __init__(self) -> None:
        super().__init__()

    async def set_level(self, level) -> None:
        """Sets the output level for the dimmer.

        Args:
            level (_type_): must be avalue between 0 and 100

        Raises:
            Exception: if the dimmer is not yet attached or the level is wrong
        """
        if not self.is_attached():
            raise Exception("Dimmer not attached to controller")
        if level < 0 or level > 100:
            raise Exception("Invalid dimmer value - must be in 0..100")
        await self.controller.set_output_value(self.outpin, level)

    async def blink(self, level: int = 100, time: float = 0.2, count: int = 1) -> None:
        """makes the attached lamp blink

        Args:
            level (int, optional): the brightness (see level). Defaults to 100.
            time (float, optional): the interval duration. Defaults to 0.2.
            count (int, optional): the number ob blinks. Defaults to 1.

        Raises:
            Exception: if one of the given values is invalid or the dimmer is not attached to the controller
        """
        if not self.is_attached():
            raise Exception("Dimmer not attached to controller")
        if level < 0 or level > 100:
            raise Exception("Invalid dimmer value - must be in 0..100")
        if time <= 0.0:
            raise Exception("Invalid blink time - must be greater than 0.0")
        if count <= 0:
            raise Exception("Invalid count - must be greater than 0")
        for c in range(count):
            await self.controller.set_output_value(self.outpin, level)
            await asyncio.sleep(time)
            await self.controller.set_output_value(self.outpin, 0)
            if c < count - 1:
                await asyncio.sleep(time)


class MotorXS(OutputPart):
    """represents a motor that is attachd to one of the outputs. The motor accepts RPM-values rather than 'levels'"""
    
    MAX_RPM = 5000
    """maximum rounds per minute"""
    FORWARD = True
    """direction constant for the motor representing forward run"""
    
    BACKWARD = False
    """direction constant for the motor representing backward run"""

    def __init__(self) -> None:
        super().__init__()

    def _level_to_rpm(self, level) -> int:
        return int(level * MotorXS.MAX_RPM / 100)

    def _rpm_to_level(self, rpm) -> int:
        return int(rpm / MotorXS.MAX_RPM * 100)

    async def run_at(self, speed: int, direction: bool = FORWARD, time: float = 0.0) -> None:
        """run the motor at the given speed and direction for the given time.

        Args:
            speed (int): the speed in RPM (must be in 0..MAX_RPM)
            direction (bool, optional): the direction. Defaults to FORWARD.
            time (float, optional): if specified, the motor is automaticallly stopped after that time. Defaults to 0.0.

        Raises:
            Exception: if one of the parameters is invalid or the motor is not attached to the controller
        """
        if not self.is_attached():
            raise Exception("Motor not attached to controller")
        if speed < 0 or speed > MotorXS.MAX_RPM:
            raise Exception("Invalid speed value - must be in 0.." + str(MotorXS.MAX_RPM))
        if time < 0.0:
            raise Exception("time must be greater or equal to 0.0")
        level = self._rpm_to_level(speed)
        if direction == MotorXS.BACKWARD:
            level = -level
        await self.controller.set_output_value(self.outpin, level)
        if time > 0.0:
            await asyncio.sleep(time)
            await self.controller.set_output_value(self.outpin, 0)
