import asyncio
from btsmart import discover_controller, BTSmartController, LEDMode, Input, Output

btSmart: BTSmartController = None
    
async def on_input_change(input, value):
    global btSmart
    print("Input", input, "changed to", value)
    if value < 100:
        await btSmart.set_output_value(Output.O1, 100)
        await btSmart.set_led(LEDMode.BLUE)
    else:
        await btSmart.set_output_value(Output.O1, 0)
        await btSmart.set_led(LEDMode.YELLOW)

async def main():

    global btSmart

    btSmart = await discover_controller()
    
    print("controller", btSmart)
    
    if btSmart is None:
        raise Exception("Not found")
    print("found")

    btSmart.on_input_change(Input.I1, on_input_change)
    
    await btSmart.connect()
    print("connected")
    loop = asyncio.get_event_loop()
    await asyncio.sleep(10)
    await btSmart.disconnect()
    print("disconnected")

asyncio.run(main())