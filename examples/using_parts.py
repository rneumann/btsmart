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