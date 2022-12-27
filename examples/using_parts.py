import asyncio
from btsmart import BTSmartController
from btsmart import Button, Dimmer, MotorXM

btn = Button()
dim = Dimmer()
motor = MotorXM()

async def butten_pressed():
    print("Button pressed")
    await asyncio.gather(
        dim.set_level(100),
        motor.run_at(speed=150, time=0.5)
    )

async def butten_released():
    print("Button released")
    await dim.set_level(0)

async def main():

    btSmart = await BTSmartController.discover()

    if btSmart is not None:
        await btSmart.connect()

        btn.pressed = butten_pressed
        btn.released = butten_released

        btn.attach(btSmart, 1)
        dim.attach(btSmart, 1)
        motor.attach(btSmart, 2)

        await asyncio.sleep(30)

        await btSmart.disconnect()

asyncio.run(main())