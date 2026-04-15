from network import WLAN,STA_IF
from json import load
from time import sleep
from machine import Pin
#from picozero.picozero import pico_led

class Wifi:
    def __init__(self):
        try:
            self.led = Pin("LED", Pin.OUT)
            self.led.value(0)
            f = open('./wifi_creds.json')
            self.data = load(f)
            for credentials in self.data['Credentials']:
                print(f'SSID: {credentials['SSID']} Password: {credentials['Password']}')
        except Exception as e:
            print(f'Exception: {e}')
        self.wlan = None
    
    def connect(self):
        # Continually loop until a connection is established
        while True:
            for credentials in self.data['Credentials']:
                print(f'Attempting to connect to {credentials['SSID']}')
                retry_count = 0
                self.wlan = WLAN(STA_IF)
                self.wlan.active(True)
                self.wlan.connect(credentials['SSID'], credentials['Password'])
                while (self.wlan.isconnected() == False) and (retry_count < 10):
                    print(f'Waiting for connection...Attempt {retry_count}')
                    retry_count = retry_count + 1
                    sleep(5)
                if retry_count == 10:
                    print(f'Cannot connect to {credentials['SSID']} - retries exceeded')
                else:
                    ip = self.wlan.ifconfig()[0]
                    print(f'Connected on {ip}')
                    self.led.value(1)
                    state = 'ON'
                    return ip
                
    def disconnect(self):
        if ( self.wlan.isconnected() ):
            self.wlan.disconnect()
            
    def is_connected(self):
        return self.wlan.isconnected()
                   
if __name__ == "__main__":
    my_wifi = Wifi()
    my_wifi.connect()
    