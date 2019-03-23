# M5Stack + Honeywell PM2.5

![alt text](https://raw.githubusercontent.com/engineersmy/hazewatch_kl/implementations/m5stack/DSC03877.JPG)


The M5Stack is a microcontroller based on ESP32, by default have micropython on board and it is arduino compatible. The code to read from the HPM Sensor is written with micropython. 

## Bill of Material

* M5Stack Fire - RM207.29(USD51)
* Honeywell HPM Sensor - RM209.00(USD51.42)

## Source code 

Source code is written with micropython, can be found in src directory

## Usage and setup. 

Note that favoriot api service, you will need to register this first. Still trying to figure out how to have people contribute data to a central repository.

* Change the settings in `hazeconf.json`
* copy `hazeconf.json` to `/flash`
`ampy --port /dev/ttyUSB0 put hazeconf.json /flash/hazeconf.json`
* copy `cytron_pm25.py` to `/flash/apps/`
`ampy --port /dev/ttyUSB0 put cytron_pm25.py /flash/apps/cytron_pm25.py`
* You should be able to see `cytron_pm25` under apps

![alt text](https://raw.githubusercontent.com/engineersmy/hazewatch_kl/implementations/m5stack/IMG_20190318_214619.jpg)

## Random note

* It is possible to change the M5Stack type with only a core and m5go
* It is also possible to adapt this code to ESP32 and ESP8266
