from m5stack import *
from m5ui import *
from machine import UART
import time
import struct
import network
import urequests
import ujson


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

while not wlan.isconnected():
    lcd.print("connecting", 20, 20)
    lcd.clear()

if wlan.isconnected():
    # This is the only UART that works. 
    uart2 = UART(1, tx=17, rx=16)
    uart2.init(9600)
    while True:
        # Making data display more reasonable
        time.sleep_ms(750)
        lcd.clear()
        try:
            pm25, pm100 = fetch_sensor(uart2)
            #output = "PM 2.5 = {pm25}".format(pm25=pm25)
            lcd.print(pm25, 20, 30)
            lcd.print(pm100, 20, 40)
        except SensorException as e:
            lcd.print("There is an error", 20, 50)
            lcd.print(str(e))
            continue
        lcd.print("posting", 20, 50)
        try:
            if config.get("influxdb"):
                coord_x = config["coord_x"]
                coord_y = config["coord_y"]
                data = "measurement pm25={pm25},pm10={pm10},x={coord_x},y={coord_y}".format(pm25=pm25, pm10=pm10, coord_x=coord_x, coord_y=coord_y)
                headers = {} 
            else:
                headers = {"apikey":config["apikey"]}
                data = {
                    "device_developer_id":config["device_id"],
                    "data": {"pm2.5": pm25, "pm10":pm100}
                }
            r = urequests.post(config["endpoint"], headers=headers, json=data)
            lcd.print(endpoint, 20, 60)
            lcd.print(r.status_code, 20, 70)
            result = r.json()
            lcd.print(result["status"], 20, 80)
            # be nice send data every 10 minute
            time.sleep(60)

        except Exception as e:
            lcd.print(str(e), 20, 90)
