#
# this sample just connects to the bt-smart and call some APIs
#

import asyncio
from btsmart import BTSmartController, LEDMode, LED_LABEL, InputMode, InputMeasurement, INPUT_MODE_LABEL

async def main():

    print("searching for controller...")
     
    btSmart: BTSmartController = None
    try:
        btSmart = await BTSmartController.discover()
    except Exception as e:
        print("unable to find controller - press the button")
        return

    def disconnect():
        print("controller was disconnected")

    btSmart.on_disconnect(disconnect)

    
    # run through the APIs

    print("connecting...")
    await btSmart.connect()
    print("...done")
    
    print("device information:")
    print(await btSmart.get_device_information())

    lvl = await btSmart.get_battery_level()
    print("battery level:" + str(lvl))
    
    print("LED:")
    color = LED_LABEL[await btSmart.get_led()]
    print("color", color)
    print("setting to orange...")
    await btSmart.set_led(LEDMode.ORANGE)
    color = LED_LABEL[await btSmart.get_led()]
    print("color", color)

    print("Reading inputs...")
    for i in range(1, 5):
        r = await btSmart.get_input_value(i, InputMode.RESISTANCE)
        u = await btSmart.get_input_value(i, InputMode.VOLTAGE)
        print("Input ", i, " - R:", r, "U:", u)

    print("disconnecting...")
    await btSmart.disconnect()


    print("reconnecting...")
    await btSmart.connect()

    print("Setting the outputs...")
    for i in range(1, 3):
        for l in range(-10,11):
            await btSmart.set_output_value(i, l*10)
            await asyncio.sleep(0.1)
            v = await btSmart.get_output_value(i)
            print("Output ", i, ":", v)
        await btSmart.set_output_value(i, 0)

    print("disconnecting...")
    await btSmart.disconnect()

    print("finished tests")

asyncio.run(main())
