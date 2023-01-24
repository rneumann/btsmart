import asyncio

from pyftdi.usbtools import UsbTools, UsbDeviceDescriptor
from pyftdi.ftdi import Ftdi

from .controller import LEDMode, Input, InputMode, INPUT_MODE_UNIT, InputMeasurement, Output, BTSmartController



class BTSmartFTDI:
    
    _SOF = bytes.fromhex('5AA5')

    _CMD_GET_INFO = bytes.fromhex('03415A41')
    _CMD_GET_INPUTS = bytes.fromhex('F48A1632')
    _CMD_CFG_INPUTS = bytes.fromhex('1434FF93')
    _CMD_SET_OUTPUT = bytes.fromhex('68CE2A04')
    _CMD_REPLY = bytes.fromhex('9C0009A5')
    _CMD_SEARCH = bytes.fromhex('D0AA8326')
    _CMD_TESTMODE = bytes.fromhex('4EC54EF7')
    _CMD_SET_LED = bytes.fromhex('904CC3D8')
    _CMD_CFG_INPUTS_EX = bytes.fromhex('77F26519')
    _CMD_IO_CYCLE = bytes.fromhex('3578265A')
    _CMD_GET_BTNS = bytes.fromhex('56221DC0')

    _CFG_UINT16 = bytes(b'\x00')
    _CFG_INT16 = bytes(b'\x01')
    _CFG_UINT8 = bytes(b'\x02')
    _CFG_INT8 = bytes(b'\x03')

    _CFG_IN_VOLT = bytes(b'\x0A')
    _CFG_IN_OHM = bytes(b'\x0B')

    _LED_BLUE = 0
    _LED_YELLOW = 1
    _LED_GREEN = 2

    _ERR_NONE = 0
    _ERR_UNKN_CMD = 1
    _ERR_INV_CRC = 2
    _ERR_INV_FRM = 3
    _ERR_INV_CFG_OUT = 4
    _ERR_INV_VAL = 5

    def __init__(self, ftdi):
        self.ftdi = ftdi
        self._set_test_mode(True)
        self._set_led(BTSmartFTDI._LED_BLUE)
        #for i in range(0,4):
        #    self._config_input(i, BTSmartFTDI._CFG_IN_OHM)
        self._get_inputs()
        self._get_inputs()

    def _send_msg(self, msg: bytes, response_len: int):
        ftdi = self.ftdi
        #print("msg: ", msg.hex())
        l = ftdi.write_data(msg)
        if l != len(msg):
            raise Exception("could not send all the mesage bytes")
        else:
            resp = ftdi.read_data_bytes(response_len, 4)
            #print("resp: ", len(resp), " - ", resp.hex())
            if len(resp) != response_len:
                #print(resp.hex())
                raise Exception("unexpected response length, expected " + str(response_len) + " but received " + str(len(resp)))
            else:
                return resp

    def _set_test_mode(self, on: bool = False) -> bool:
        ftdi = self.ftdi
        #print("Set Test Mode")
        if on:
            onoff = b'\x01'
        else:
            onoff = b'\x00'
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_TESTMODE, bytes(b'\x00\x01'), onoff])
        resp = self._send_msg(msg, 9)
        if len(resp) == 9:
            err = int.from_bytes(resp[8:9], 'little', signed=False)
            if err != BTSmartFTDI._ERR_NONE:
                raise Exception("set test mode error" + str(err))
            else:
                return True
        else:
            return True

    def _set_led(self, led: int):
        ftdi = self.ftdi
        #print("Set LED:", led)
        led_cfg = bytearray.fromhex('000000010000020000')
        if led == BTSmartFTDI._LED_BLUE:
            led_cfg[2] = 1
        if led == BTSmartFTDI._LED_YELLOW:
            led_cfg[5] = 1
        if led == BTSmartFTDI._LED_GREEN:
            led_cfg[8] = 1
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_SET_LED, bytes(b'\x00\x09'), led_cfg])
        resp = self._send_msg(msg, 9)
        if len(resp) == 9:
            err = int.from_bytes(resp[8:9], 'little', signed=False)
            if err != BTSmartFTDI._ERR_NONE:
                raise Exception("set led mode error" + str(err))
            else:
                return True
        else:
            return True

    def _get_information(self) -> bytes:
        ftdi = self.ftdi
        #print("Get Information")
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_GET_INFO, bytes(b'\x00\x00')])
        return self._send_msg(msg, 15)

    def _config_input(self, input: int, mode: int) -> bool:
        ftdi = self.ftdi
        #print("Config Input", input, mode, type(mode))
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_CFG_INPUTS, b'\x00\x02', input.to_bytes(1, 'little'), mode.to_bytes(1, 'little', signed=False)])
        resp = self._send_msg(msg, 9)
        if len(resp) == 9:
            err = int.from_bytes(resp[8:9], 'little', signed=False)
            if err != BTSmartFTDI._ERR_NONE:
                raise Exception("configuration error" + str(err))
            else:
                return True
        else:
            return True

    def _get_inputs(self):
        ftdi = self.ftdi
        #print("Get Inputs")
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_GET_INPUTS, bytes(b'\x00\x00')])
        response = self._send_msg(msg, 8+5*4)
        result = [None, None, None, None]
        for i in range(0, 4):
            p = 8+(i*4)
            n = int(response[p])
            c = response[p+1]
            v = int.from_bytes(response[p+2:p+4], 'little', signed=False)
            result[n] = { 'cfg': c, 'val': v }
        return result

    def _set_output(self, output: int, value: int):
        ftdi = self.ftdi
        #print("Set Output")
        msg = b"".join([BTSmartFTDI._SOF, BTSmartFTDI._CMD_SET_OUTPUT, bytes(b'\x00\x04'), output.to_bytes(1, 'little', signed=False), BTSmartFTDI._CFG_INT8, b'\x00', value.to_bytes(1, 'little', signed=True)])
        resp = self._send_msg(msg, 9)
        if len(resp) == 9:
            err = int.from_bytes(resp[8:9], 'little', signed=False)
            if err != BTSmartFTDI._ERR_NONE:
                raise Exception("configuration error" + str(err))
            else:
                return True
        else:
            return True


class BTSmartController_USB(BTSmartController):
    """This class represents a BTSmart-Controller attached via USB-cable"""
    
    _POLL_INTERVAL: float = 0.05

    async def discover() -> BTSmartController:
        dd = UsbDeviceDescriptor(8733, 5, None, None, None, 0, None)
        try:
            #print("Looking for:", dd)
            dev = UsbTools.get_device(dd)
            #print("Found:", dev)
            if dev is None:
                return None
            ftdi = Ftdi()
            ftdi.open_from_device(dev, 1)
            ftdi.set_baudrate(115200)
            btFtdi = BTSmartFTDI(ftdi)
            #print("FTDI:", ftdi)
            return BTSmartController_USB(btFtdi)
        except:
            return None
        

    def __init__(self, dev: BTSmartFTDI) -> None:
        super().__init__()
        self._is_polling = False
        self.task : asyncio.Task = None
        self.dev = dev
        self._led = LEDMode.BLUE
        self._outputs = [0, 0]
        self._inputs = dev._get_inputs()

    def is_connected(self) -> bool:
        return self._is_polling

    async def _poll_state(self):
        print("started coroutine")
        self._is_polling = True
        print("polling: ", self._is_polling)
        while self._is_polling:
            #print(".")
            await self._update_inputs()
            await asyncio.sleep(BTSmartController_USB._POLL_INTERVAL)
        print("coroutine ended")
            
    async def connect(self) -> bool:
        await self.reset()
        self.dev._set_test_mode()
        await asyncio.sleep(0)
        print("started polling")
        loop = asyncio.get_event_loop()
        self.task = loop.create_task(self._poll_state(), name='BTSmartController USB update')
        return True
    
    async def disconnect(self) -> None:
        self._is_polling = False
        print("stopped polling")
        return

    async def get_device_information(self) -> dict[str, str]:
        # TODO: implement this
        return {}

    async def get_battery_level(self) -> int:
        # TODO: implement this
        return 100

    async def set_led(self, led: LEDMode) -> None:
        self.dev._set_led(led._value_)
        self._led = led

    async def get_led(self) -> LEDMode:
        return self._led

    async def _update_inputs(self):
        #print("u")
        old_inputs = self._inputs
        self._inputs = self.dev._get_inputs()
        for input in Input.all():
            i = input.value
            oldI = old_inputs[i]
            oldV = oldI['val']
            newI = self._inputs[i]
            newV = newI['val']
            if oldV != newV:
                #print("X", i, newV)
                asyncio.create_task(self._on_input_value_changed(input, newV))

    async def set_input_mode(self, input: Input, mode: InputMode) -> None:
        self.dev._config_input(input.value, mode.value)
        await self._update_inputs()

    async def get_input_mode(self, input: Input) -> InputMode:
        if not self._is_polling:
            await self._update_inputs()
        inp = self._inputs[input.value]
        if inp['cfg'] == BTSmartFTDI._CFG_IN_VOLT:
            return InputMode.VOLTAGE
        else:
            return InputMode.RESISTANCE

    async def get_input_value(self, input: Input, mode: InputMode = None) -> InputMeasurement:
        inp = self._inputs[input.value]
        if inp['cfg'] == BTSmartFTDI._CFG_IN_VOLT:
            m = InputMode.VOLTAGE
        else:
            m = InputMode.RESISTANCE
        if m != mode:
            print("switching mode to", mode)
        else:
            if not self._is_polling:
                await self._update_inputs()
        inp = self._inputs[input.value]
        return InputMeasurement(inp['val'], mode)

    async def set_output_value(self, output: Output, value: int) -> None:
        if value < int(-100) or value > int(100):
            raise Exception("motor output must be in -100..100")
        self.dev._set_output(output.value, value)
        self._outputs[output.value] = value

    async def get_output_value(self, output: Output) -> int:
        return self._outputs[output.value]
    