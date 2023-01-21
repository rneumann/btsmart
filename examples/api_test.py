#
# this sample just connects to the bt-smart and call some APIs
#

import asyncio
from btsmart import discover_controller, BTSmartController, LEDMode, LED_LABEL, Input, InputMode, InputMeasurement, INPUT_MODE_LABEL, Output


btSmart: BTSmartController = None
    

def disconnect():
    print("controller was disconnected")


async def main():

    global btSmart

    print("searching for controller...")
     
    btSmart = await discover_controller()
    
    if btSmart is None:
        print("no controller found")
        return

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
    #color = LED_LABEL[await btSmart.get_led()]
    #print("color", color)
    
    for led in [LEDMode.BLUE, LEDMode.GREEN, LEDMode.YELLOW]:
        print("setting to", LED_LABEL[led], "...")
        await btSmart.set_led(led)
        await asyncio.sleep(0.5)
        #color = LED_LABEL[await btSmart.get_led()]
        #print("color", color)

    print("Reading inputs...")
    for i in Input.all():
        r = await btSmart.get_input_value(i, InputMode.RESISTANCE)
        u = await btSmart.get_input_value(i, InputMode.VOLTAGE)
        print("Input ", i, " - R:", r, "U:", u)

    print("disconnecting...")
    await btSmart.disconnect()


    print("reconnecting...")
    await btSmart.connect()

    print("Setting the outputs...")
    for o in Output.all():
        for l in range(-10,11):
            await btSmart.set_output_value(o, l*10)
            await asyncio.sleep(0.1)
            v = await btSmart.get_output_value(o)
            print("Output ", o, ":", v)
        await btSmart.set_output_value(o, 0)

    print("disconnecting...")
    await btSmart.disconnect()

    print("finished tests")

asyncio.run(main())
