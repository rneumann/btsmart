import asyncio
from btsmart import discover_controller, BTSmartController, Input, Output
from btsmart import Button, Dimmer, MotorXS

btn = Button()
dim = Dimmer()
motor = MotorXS()

async def button_pressed():
    print("Button pressed")
    await asyncio.gather(
        dim.set_level(100),
        motor.run_at(speed=3500, time=0.5)
    )

async def button_released():
    print("Button released")
    await dim.set_level(0)

btn.on_press(button_pressed)
btn.on_release(button_released)

async def main():

    btSmart: BTSmartController = await discover_controller()

    if btSmart is None:
        print("No controller found - please press the connect button on the device")
        return

    btn.attach(btSmart, Input.I1)
    dim.attach(btSmart, Output.O1)
    motor.attach(btSmart, Output.O2)

    await btSmart.connect()

    await asyncio.sleep(20)

    await btSmart.disconnect()

asyncio.run(main())