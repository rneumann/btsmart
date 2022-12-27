import asyncio
from btsmart.controller import BTSmartController, LED_Mode, InputMode, InputMeasurement

#------------------------------------------------------------------------------------------------------------

async def main():

    btSmart = None
    try:
        btSmart = await BTSmartController.discover()
        #btSmart = await BTSmartController.find("E709050F-1FC3-E7E5-5673-AE53568A1425")
    except Exception as e:
        print("unable to find controller - press the button")
        print(e)

    if btSmart is not None:
        await btSmart.connect()
        print("Device Information", await btSmart.get_device_information())

        led = await btSmart.get_led()
        print("led: ", led)
        await btSmart.set_led(LED_Mode.BLUE)
        await asyncio.sleep(0.5)
        await btSmart.set_led(LED_Mode.ORANGE)

        await btSmart.set_input_mode(2, InputMode.VOLTAGE)
        await btSmart.set_input_mode(4, InputMode.VOLTAGE)

        async def on_input_change(num, value):
            print("Input", num, "changed to", value)
            if value < 100:
                await btSmart.set_output_value(1, 100)
                await btSmart.set_led(LED_Mode.BLUE)
            else:
                await btSmart.set_output_value(1, 0)
                await btSmart.set_led(LED_Mode.ORANGE)
            #measures = ""
            #for j in range(1,5):
            #    m: InputMeasurement = await btSmart.get_input(j, InputUnit.RESISTANCE)
            #    measures = measures + str(j) + ": " + str(m) + ";   "
            #print(">>", measures)

        btSmart.on_input_change(1, on_input_change)


        await asyncio.sleep(10)

        """
        m1Val = 0

        for i in range(20):
            measures = ""
            for j in range(1,5):
                m: InputMeasurement = await btSmart.get_input(j, InputUnit.RESISTANCE)
                measures = measures + str(j) + ": " + str(m) + ";   "

            print(i, ">>", measures)

            m1Val = 100 - m1Val
            await btSmart.set_output_value(1, m1Val)
            #await btSmart.set_output_value(2, m1Val)
            print("output 1: ", await btSmart.get_output_value(1))

            await asyncio.sleep(0.2)


        """

        await btSmart.disconnect()

asyncio.run(main())