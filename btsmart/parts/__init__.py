# -*- coding: utf-8 -*-
"""
Ths module provides convenience classes to easily represent built scenarios and
according logic.

@Author: Rainer Neumann
@Date: 2022-12-26

Todo:
    * Add more convenience functionality - more parts
    * Needs a lot more tests
    * blink in Dimmer does not yet work

"""

import asyncio
from btsmart.controller import BTSmartController

class ElectronicsPart:
    def __init__(self) -> None:
        self.controller: BTSmartController = None

    def is_attached(self) -> bool:
        return self.controller is not None


class InputPart(ElectronicsPart):
    def __init__(self) -> None:
        super().__init__()
        self.inputValueChanged = None
        self.lastValue: int = None

    def attach(self, ctrl: BTSmartController, number: int) -> None:
        if ctrl is None:
            raise Exception("cannot attach InputPart to 'None'")
        if number < 1 or number > 4:
            raise Exception("invalid input number - must be in 1..4")
        ctrl.on_input_change(number, self._on_input_change_)
        self.controller = ctrl

    async def _on_input_change_(self, num, value) -> None:
        pass


class OutputPart(ElectronicsPart):
    def __init__(self) -> None:
        super().__init__()
        self.lastValue: int = None

    def attach(self, ctrl: BTSmartController, number: int) -> None:
        if ctrl is None:
            raise Exception("cannot attach Part to 'None'")
        if number < 1 or number > 2:
            raise Exception("invalid input number - must be in 1..2")
        self.outpin = number
        self.controller = ctrl


class Switch(InputPart):
    def __init__(self) -> None:
        super().__init__()
        self.threshold = 200

    def is_open(self) -> bool:
        if self.lastValue is not None:
            return self.lastValue.value < self.threshold
        else:
            return False


class Button(Switch):
    def __init__(self) -> None:
        super().__init__()
        self.pressed = None  # callback function without parameters
        self.released = None  # callback function without parameters

    def is_pressed(self) -> bool:
        if self.lastValue is not None:
            return self.lastValue.value < self.threshold
        else:
            return False

    async def _on_input_change_(self, num, value) -> None:
        oldval = self.lastValue
        self.lastValue = value
        if value < self.threshold:
            if oldval is None or oldval > self.threshold:
                if self.pressed is not None:
                    if asyncio.iscoroutinefunction(self.pressed):
                        await self.pressed()
                    else:
                        self.pressed()
        else:
            if oldval is not None and oldval <= self.threshold:
                if self.released is not None:
                    if asyncio.iscoroutinefunction(self.pressed):
                        await self.released()
                    else:
                        self.released()


class LightBarrier(Switch):
    def __init__(self) -> None:
        super().__init__()
        self.opened = None
        self.interrupted = None

    async def _on_input_change_(self, num, value) -> None:
        oldval = self.lastValue
        self.lastValue = value
        if value < self.threshold:
            if oldval is None or oldval > self.threshold:
                if self.opened is not None:
                    self.opened()
        else:
            if oldval is not None and oldval <= self.threshold:
                if self.interrupted is not None:
                    self.interrupted()


class Dimmer(OutputPart):
    def __init__(self) -> None:
        super().__init__()
        self.outpin = 0

    async def set_level(self, level) -> None:
        if not self.is_attached():
            raise Exception("Dimmer not attached to controller")
        if self.outpin < 1 or self.outpin > 2:
            raise Exception("Dimmer not correctly attached to controller output (must be 1 or 2)")
        if level < 0 or level > 100:
            raise Exception("Invalid dimmer value - must be in 0..100")
        await self.controller.set_output_value(self.outpin, level)

    async def blink(self, level: int = 100, time: float = 0.2, count: int = 1) -> None:
        if not self.is_attached():
            raise Exception("Dimmer not attached to controller")
        if self.outpin < 1 or self.outpin > 2:
            raise Exception("Dimmer not correctly attached to controller output (must be 1 or 2)")
        if level < 0 or level > 100:
            raise Exception("Invalid dimmer value - must be in 0..100")
        if time <= 0.0:
            raise Exception("Invalid blink time - must be greater than 0.0")
        if count <= 0:
            raise Exception("Invalid count - must be greater than 0")
        for c in range(count):
            await self.controller.set_output_value(self.outpin, level)
            if c < count - 1:
                await asyncio.sleep(time)


class MotorXM(OutputPart):
    FORWARD = True
    BACKWARD = False

    def __init__(self) -> None:
        super().__init__()

    def _level_to_rpm(self, level) -> int:
        return int(level * 3.38)

    def _rpm_to_level(self, rpm) -> int:
        return int(rpm / 3.38)

    async def run_at(self, speed: int, direction: bool = FORWARD, time: float = 0.0) -> None:
        if not self.is_attached():
            raise Exception("Dimmer not attached to controller")
        if self.outpin < 1 or self.outpin > 2:
            raise Exception("Dimmer not correctly attached to controller output (must be 1 or 2)")
        if speed < 0 or speed > 338:
            raise Exception("Invalid speed value - must be in 0..338")
        if time < 0.0:
            raise Exception("time must be greater or equal to 0.0")
        level = self._rpm_to_level(speed)
        if direction == MotorXM.BACKWARD:
            level = -level
        await self.controller.set_output_value(self.outpin, level)
        if time > 0.0:
            await asyncio.sleep(time)
            await self.controller.set_output_value(self.outpin, 0)
