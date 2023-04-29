from machine import UART,Pin,deepsleep
from time import sleep,time
from pyfingerprint import PyFingerprint
from BlynkLib import Blynk
from esp32 import wake_on_ext0,WAKEUP_ALL_LOW
from network import WLAN,STA_IF
import urequests
import esp
esp.osdebug(None)
import gc
gc.collect()

wake_button = Pin(14, mode = Pin.IN, pull=Pin.PULL_UP)
lock=Pin(21,Pin.OUT)
buzz=Pin(18,Pin.OUT,pull=Pin.PULL_DOWN)
lock.value(1)
wake_on_ext0(pin = wake_button, level = WAKEUP_ALL_LOW)

re=no_activity=no_match=bly=stop=0

phone_number = '919903855585'
message1 = 'Someone+is+trying+to+enter+the+house'
message2 = 'Unauthorised+access'
api_key = '7727652'

SSID = 'MAJESTIC MOKSH'
PASS = 'Mokesh12345' 
BLYNK_AUTH = "8sFjFSiNs0AVvf4juMRc2Y63NLQLuAdq"

wifi = WLAN(STA_IF)
wifi.active(True)
try:
    wifi.connect(SSID, PASS)
    while not wifi.isconnected():
        pass
    print('Connected to WiFi')
    sleep(1)
    print('IP address: ',wifi.ifconfig()[0])
    sleep(1)
except Exception as e:
    pass

blynk = Blynk(BLYNK_AUTH)
blynk.virtual_write(1,0)
blynk.virtual_write(2,0)
blynk.virtual_write(3,0)
blynk.virtual_write(4,0)
@blynk.on("V1")
def v1_write_handler(value):
    global re
    global reason
    while True:
        try:
            if(re>5):
                blynk.virtual_write(0,"Try again later in 30 sec")
                re=1
                sleep(30)
                break
            add_fingerprint()
            if(re==0):
                break
        except:
            re=re+1
            break
    blynk.virtual_write(1,0)
@blynk.on("V2")
def v2_write_handler(value):
    clear_database()
    blynk.virtual_write(2,0)
@blynk.on("V3")
def v3_write_handler(value):
    delete_position=value[0]
    delete_fingerprint(delete_position)
    blynk.virtual_write(3,-1)
@blynk.on("V4")
def v4_write_handler(value):
    global stop
    stop=value[0]

sensorSerial = UART(1)
sensorSerial.init(57600, bits=8, parity=None, stop=1, rx=17, tx=16)
def send_message(phone_number, api_key, message):
  url = 'https://api.callmebot.com/whatsapp.php?phone='+phone_number+'&text='+message+'&apikey='+api_key
  urequests.get(url)
send_message(phone_number, api_key, message1)
f = PyFingerprint(sensorSerial)
if (f.verifyPassword()):
    blynk.virtual_write(0,"System is Live")
else:
    blynk.virtual_write(0,"System Error")
send_message(phone_number, api_key, message1)

def memory_not_free():
    for i in range(0,4):
        templateIndex = f.getTemplateIndex(i)
        for j in range(0, len(templateIndex)):
            if ( templateIndex[j] is False ):
                return False
    return True
def add_fingerprint():
    global re
    global reason
    if(memory_not_free()):
        blynk.virtual_write(0,'Memory full --> Try deleting / clearing your database')
        return
    blynk.virtual_write(0,'Waiting for finger...')
    while (f.readImage() == False):
        pass
    sleep(1)
    f.convertImage(0x01)
    result = f.searchTemplate()
    if (result[0] != -1):
        blynk.virtual_write(0,"Fingerprint exists")
        sleep(1)
        re=re+1
        return
    blynk.virtual_write(0,'Remove your fingerprint')
    sleep(1)
    blynk.virtual_write(0,'Place your finger on the sensor again...')
    sleep(1)
    blynk.virtual_write(0,'Waiting for finger...')
    while (f.readImage() == False):
        pass
    sleep(1)
    f.convertImage(0x02)
    if (f.compareCharacteristics() == 0):
        blynk.virtual_write(0,"Fingerprint does'nt match")
        sleep(1)
        re=re+1
        return
    f.createTemplate()
    stored_location=f.storeTemplate()
    blynk.virtual_write(0,('Fingerprint enrolled successfully! at position: '+str(stored_location)))
    sleep(1)
    blynk.virtual_write(0,('Remove your finger asap'))
    sleep(5)
    re=0
def delete_fingerprint(delete_position):
    f.deleteTemplate(int(delete_position))
    blynk.virtual_write(0,('Fingerprint at position '+str(delete_position)+' deleted'))
    sleep(1)
    
def clear_database():
    f.clearDatabase()
    blynk.virtual_write(0,'Database cleared')
    sleep(1)
def search_fingerprint():
    global no_match
    global no_activity
    t=time()
    blynk.virtual_write(0,'Waiting for fingerprint...')
    while ( f.readImage() == False ):
        if((t-time())>180):
            no_activity=1
            return
        pass
    sleep(1)
    blynk.virtual_write(0,'Remove your finger')
    sleep(1)
    f.convertImage(0x01)
    result = f.searchTemplate()
    stored_location = result[0]
    accuracy = result[1]
    if ( stored_location == -1 ):
        blynk.virtual_write(0,'No match found')
        buzz.value(1)
        sleep(10)
        buzz.value(0)
        no_match=no_match+1
    else:
        blynk.virtual_write(0,('Match found at position '+str(stored_location)+' with accuracy score of '+str(accuracy)))
        no_match=0
        lock.value(0)
        sleep(10)
        lock.value(1)
        blynk.virtual_write(0,'Sleeping ...')
        sleep(4)
        deepsleep(0)

while True:  
    blynk.virtual_write(0,'System is live')
    blynk.run()
    if(stop==0):
        if(f.readImage()==True):
            while True:
                try:
                    search_fingerprint() 
                    break
                except:
                    blynk.virtual_write(0,"Trying again")
                    sleep(1)
                    pass       
        if(no_activity==1):
            send_message(phone_number, api_key, message2)
            blynk.virtual_write(0,'Going to deep-sleep')
            esp.deepsleep(0)
        if(no_match==4):
            no_match=0
            stop=1
            blynk.virtual_write(4,1)
            send_message(phone_number, api_key, message1)

        
        
