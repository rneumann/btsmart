import asyncio
from btsmart import discover_controller, BTSmartController, LEDMode, Input, InputMode, InputMeasurement, Output

#------------------------------------------------------------------------------------------------------------

btSmart: BTSmartController = None

async def on_input_change(num, value):
    global btSmart
    print("Input", num, "changed to", value)
    if value < 100:
        await btSmart.set_output_value(Output.O1, 100)
        await btSmart.set_led(LEDMode.BLUE)
    else:
        await btSmart.set_output_value(Output.O1, 0)
        await btSmart.set_led(LEDMode.YELLOW)
    measures = ""
    for j in Input.all():
        m: InputMeasurement = await btSmart.get_input_value(j, InputMode.RESISTANCE)
        measures = measures + str(j) + ": " + str(m) + ";   "
    print(">>", measures)

async def main():

    global btSmart

    btSmart = await discover_controller()

    if btSmart is None:
        print("unable to find controller - press the button or connect USB-cable")
        return

    await btSmart.connect()
    print("Device Information", await btSmart.get_device_information())

    led = await btSmart.get_led()
    print("led: ", led)
    await btSmart.set_led(LEDMode.BLUE)
    await asyncio.sleep(0.5)
    await btSmart.set_led(LEDMode.GREEN)
    await asyncio.sleep(0.5)
    await btSmart.set_led(LEDMode.YELLOW)

    await btSmart.set_input_mode(Input.I2, InputMode.VOLTAGE)
    await btSmart.set_input_mode(Input.I4, InputMode.VOLTAGE)

    btSmart.on_input_change(Input.I1, on_input_change)

    await asyncio.sleep(10)

    await btSmart.disconnect()

asyncio.run(main())