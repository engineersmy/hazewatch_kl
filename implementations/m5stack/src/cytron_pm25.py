from m5stack import *
from m5ui import *
from machine import UART
import time
import struct
import network
import urequests
import ujson
import ubinascii

class SensorException(Exception):
    pass


def fetch_sensor(uart2):
    # The command to start measurement
    # source https://sensing.honeywell.com/honeywell-sensing-hpm-series-particle-sensors-datasheet-32322550-e-en.pdf
    # Page 5
    uart2.write('\x68\x01\x01\x96')
    data=uart2.read(32)
    # Opps there is problem, 
    # call the command to stop measurement every time there is problem
    if not data:
        uart2.write('\x68\x01\x02\x95')
        raise SensorException("There is no data")
    # Should only have 32 bit of data
    if len(data) != 32:
        uart2.write('\x68\x01\x02\x95')
        raise SensorException("Data length is wrong")
    # measurement must start with 0x42
    if data[0] != 0x42:
        uart2.write('\x68\x01\x02\x95')
        raise SensorException("Data is wrong format")
    l = list(data)
    # The number is big endian. Also drop the first 4 byte
    # Covert the rest into 14 number
    frame = struct.unpack(">HHHHHHHHHHHHHH", bytes(l[4:]))
    # I really only care about frame[1] and frame[2]. WHich is PM2.5 and PM10
    # Source https://sensing.honeywell.com/honeywell-sensing-hpm-series-particle-sensors-datasheet-32322550-e-en.pdf
    # Page 6
    pm25=frame[1]
    pm100=frame[2]
    return (pm25, pm100)

# load config
f = open("/flash/hazeconf.json")
config = ujson.loads(f.read())

# setup wifi
wlan = network.WLAN(network.STA_IF)
wlan.active(True)
wlan.connect(config["ssid"],config["password"])

uart2 = UART(1, tx=17, rx=16)
uart2.init(9600)

CONNECTED = False
SUBMITTED = False
INITIAL = True

# Why 100 than 10? because 25 is 2.5 * 10
pm25 = 0
pm100 = 100
lcd.clear()
conn_status = M5Circle(40, 10, 10, lcd.RED)

pm25_label = M5TextBox(62, 40, "PM 2.5", lcd.FONT_DefaultSmall, 0xFFFFFF)
pm100_label = M5TextBox(163, 40, "PM 10", lcd.FONT_DefaultSmall, 0xFFFFFF)
pm25_text = M5TextBox(62, 66, str(pm25), lcd.FONT_DejaVu24, 0xFFFFFF)
pm100_text = M5TextBox(163, 66, str(pm100), lcd.FONT_DejaVu24, 0xFFFFFF)
last_ticks = time.ticks_ms()

while True:
    # Making data display more reasonable
    if wlan.isconnected():
        conn_status.setBgColor(lcd.YELLOW)
    else:
        conn_status.setBgColor(lcd.RED)

    if not INITIAL:
        current_ticks = time.ticks_ms()
        if time.ticks_diff(current_ticks, last_ticks) < 300000:
            continue
        last_ticks = time.ticks_ms()

    try:
        pm25, pm100 = fetch_sensor(uart2)
        pm25_text.setText(str(pm25))
        pm100_text.setText(str(pm100))
    except SensorException as e:
        pm25_text.setText("err")
        pm100_text.setText("err")
        continue
    INITIAL = False
    # Only post if connected
    if wlan.isconnected():
        try:
            if config.get("influxdb"):
                coord_x = config["coord_x"]
                coord_y = config["coord_y"]

                data = "pmvalue,id={id} pm25={pm25},pm10={pm10},x={coord_x},y={coord_y}".format(pm25=pm25, pm10=pm100, coord_x=coord_x, coord_y=coord_y, id={mac_addr})
                r = urequests.post(config["endpoint"], data=data)
            else:
                headers = {"apikey":config["apikey"]}
                data = {
                    "device_developer_id":config["device_id"],
                    "data": {"pm2.5": pm25, "pm10":pm100}
                }
                r = urequests.post(config["endpoint"], headers=headers, json=data)
            conn_status.setBgColor(lcd.GREEN)
            # be nice send data every 10 minute

        except Exception as e:
            conn_status.setBgColor(lcd.YELLOW)
