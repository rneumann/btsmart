========
BT-Smart
========

:Authors:
    Prof. Dr. Rainer Neumann

:Version: 0.1.6 of 2022/12/28

A small library that helps to build simple projects based on the Fischertechnik BT-Smart Controller
using Bluetooth LE.
The library uses the bleak libray to handle the BLE protocol and asyncio to access device features.

Installation
------------

pip install btsmart

Getting Started
---------------

Assume we have attached a Button to the first input of the Controller, as simple lamp to output 1 and a motor element to output 2.
Then we can use the library like this

.. code-block:: python

    import asyncio
    from btsmart import BTSmartController
    from btsmart import Button, Dimmer, MotorXM

    btn = Button()
    dim = Dimmer()
    motor = MotorXM()

    async def button_pressed():
        print("Button pressed")
        await asyncio.gather(
            dim.set_level(100),
            motor.run_at(speed=150, time=0.5)
        )

    async def button_released():
        print("Button released")
        await dim.set_level(0)

    btn.on_press(button_pressed)
    btn.on_release(button_released)

    async def main():

        btSmart: BTSmartController = None
        try:
            btSmart = await BTSmartController.discover()
        except Exception:
            print("No controller found - please press the connect button on the device")
            return

        btn.attach(btSmart, 1)
        dim.attach(btSmart, 1)
        motor.attach(btSmart, 2)

        await btSmart.connect()

        await asyncio.sleep(20)

        await btSmart.disconnect()

    asyncio.run(main())
