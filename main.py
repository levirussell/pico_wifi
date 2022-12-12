# File must be named "main.py" on pico to run on boot

import time
import utime
import ntptime
import network
import urequests as requests
import json
from machine import Pin
import machine
from secret import secret

# PICO-W on board LED (Uses different pinout than non-wifi PICO)
led = Pin("LED", Pin.OUT)

ssid = secret['ssid']
pw = secret['pw']

wlan = network.WLAN(network.STA_IF)

network_connected = False

def connect_to_wifi():
    wlan.active(True)
    time.sleep(1)
    wlan.connect(ssid, pw)

    # Wait for connect or fail
    max_wait = 20
    while max_wait > 0:
        if wlan.status() < 0 or wlan.status() >= 3:
            break
        max_wait -= 1
        print('waiting for connection...')
        time.sleep(1)

def get_timezone():
    url = 'http://ip-api.com/json'
    request = requests.get(url)
    data = json.loads(request.text)
    return data

def get_timezone_offset():
    tz = get_timezone()
    url = 'http://worldtimeapi.org/api/timezone/' + tz['timezone']
    request = requests.get(url)
    data = json.loads(request.text)
    return data
 
while not network_connected:
    led.on()
    connect_to_wifi()
    # Handle connection error
    if wlan.status() != 3:
        # continue instead of throw error because first connection will usually fail
        continue
        # RuntimeError('network connection failed')
    else:
        print('wifi connected')
        status = wlan.ifconfig()
        print( 'ip = ' + status[0])
        led.off()
        network_connected = True
        try:
            time_data = get_timezone_offset()
            print("Local time before synchronization：%s" %str(time.localtime()))

            ntptime.settime()
            rtc = machine.RTC()
            tm = utime.localtime(utime.mktime(utime.localtime()) + time_data['raw_offset'])
            tm = tm[0:3] + (0,) + tm[3:6] + (0,)
            rtc.datetime(tm)
            print("Local time after synchronization：%s" %str(time.localtime()))
        except Exception as e:
            print("Error syncing time", e)
            