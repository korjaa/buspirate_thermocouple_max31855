import re
import struct
import time
import serial
from pexpect_serial import SerialSpawn
import logging

logger = logging.getLogger(__name__)

class MAX31855:
    re_bytes = re.compile(r".*READ: (0x[0-9A-F]{2} )(0x[0-9A-F]{2} )(0x[0-9A-F]{2} )(0x[0-9A-F]{2} )", re.DOTALL)

    def __init__(self, port: str):
        self.port = port
        self.ser = serial.Serial(self.port, 115200, timeout=0)
        logger.info(f"Created {self.port}")

        self.ss = None

    def __enter__(self, ):
        #self.ser.open()
        logger.info(f"Opening {self.port}")

        self.ss = SerialSpawn(self.ser, encoding="utf-8")
        self.ss.sendline('#')
        self.ss.expect('Bus Pirate v3')

        self.ss.sendline("m")

        self.ss.expect("exit")
        # 1. HiZ
        # 2. 1-WIRE
        # 3. UART
        # 4. I2C
        # 5. SPI
        # 6. 2WIRE
        # 7. 3WIRE
        # 8. LCD
        # 9. DIO
        # x. exit(without change)
        self.ss.sendline("5")

        self.ss.expect("Set speed:")
        # 1. 30KHz
        # 2. 125KHz
        # 3. 250KHz
        # 4. 1MHz
        self.ss.sendline("1")

        self.ss.expect("Clock polarity:")
        # 1. Idle low *default
        # 2. Idle high
        self.ss.sendline("1")

        self.ss.expect("Output clock edge:")
        # 1. Idle to active
        # 2. Active to idle *default
        self.ss.sendline("2")

        self.ss.expect("Input sample phase:")
        # 1. Middle *default
        # 2. End
        self.ss.sendline("1")

        self.ss.expect("CS:")
        # 1. CS
        # 2. /CS *default
        self.ss.sendline("2")

        self.ss.expect("Select output type:")
        # 1. Open drain (H=Hi-Z, L=GND)
        # 2. Normal (H=3.3V, L=GND)
        self.ss.sendline("2")

        self.ss.expect("Ready")

        # Enable supplies
        self.ss.sendline("W")
        self.ss.expect("Power supplies ON")
        time.sleep(0.5)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Shutdown supplies
        #self.ss.sendline("w")
        #self.ss.expect("Power supplies OFF")

        # Reset buspirate
        self.ss.sendline("#")
        self.ss.expect('Bus Pirate v3')

        # Close serial port
        logger.info(f"Closing {self.port}")
        self.ser.close()

    def read(self) -> float:
        # Read SPI bus
        self.ss.sendline("[r:4]")
        self.ss.expect("/CS DISABLED")

        match = self.re_bytes.match(self.ss.before)
        byts = bytes(int(v, 0) for v in match.groups())
        value = struct.unpack(">L", byts)[0]
        bits = f"{value:032b}"[::-1]
        temperature = int(bits[31:18-1:-1], 2) * 0.25
        return temperature

with MAX31855(port='/dev/ttyUSB0') as max:
    try:
        while True:
            print(max.read())
            time.sleep(0.1)
    except KeyboardInterrupt:
        pass
