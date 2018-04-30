import RPi.GPIO as GPIO
import time
import TempHeader1
import serial
import subprocess

dev = subprocess.check_output('ls /dev/ttyACM*', shell=True) #find out what name the Arduino is under
print (dev) #display Arduino name (will be shown in bytes)
dev=dev.decode("utf-8") #convert Arduino name from bytes to string
dev=dev.replace("\n","") #get rid of \n

try:
    ser = serial.Serial(dev,9600) # Connect to Arduino's Serial
    print ("Connected to Arduino")
except:
    print ("Arduino not connected")

###########################################################################################
tempsensor = TempHeader1.temp_sensor()#Create MCP9808 temp sensor object
###########################################################################################

###########################################################################################
timer = 0 #inital timer value. Timer will be in seconds
last_alert = 0 #time since last alert
danger_rate = .3
last_temp = 0 # keep track of last temp measurement
base_temp = 0
base_time = 0
temp_rate = 0 #difference between current and last temperature
start = 0 #will be zero only for timer = 1
onbutton = 40 #onbutton connected pin40 on rpi
offbutton= 38 #offbutton connected to pin 38 on rpi
timer_speed = 1 #timer iterates once/second
max = 89 #maximum temperature
#########################################################################################


print("Current Temperature is: %.2f F" %tempsensor.readTempF())      
print("Maximum car temperature is: " + str(max))

GPIO.setmode(GPIO.BOARD)
GPIO.setup(onbutton,GPIO.IN) #onbutton represents parent leaving BLE range
GPIO.setup(offbutton,GPIO.IN) #offbutton represents parent returning to BLE Range


while True:
    if (GPIO.input(onbutton) == 1 ) & ( GPIO.input(offbutton) == 0 ): #if ONLY the onbutton is pushed
        print("OnButton Pressed")
        
        while (GPIO.input(offbutton) == 0) :# offbutton isn't pushed (parent hasn't returned)
            print(timer)
            temperature = tempsensor.Temperature(base_temp, base_time, timer, start, danger_rate, last_alert, ser)
            
            #Update values
            base_temp = temperature['base_temp']
            base_time = temperature['base_time']
            start = temperature['start']
            last_alert = temperature['last_alert']
            
            time.sleep(timer_speed) # wait for ___ seconds
            timer = timer + 1
            
            if GPIO.input(offbutton) == 1 : # If offbutton is pushed (parent returns within BLE range)
                timer = 0 #start timer over
                break
        
    if(GPIO.input(offbutton) == 1 ) & (GPIO.input(onbutton) == 0): #if ONLY the offbutton is pushed
        print("OffButton Pressed")
        time.sleep(1)