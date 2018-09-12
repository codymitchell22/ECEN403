#!/usr/bin/python
import RPi.GPIO as GPIO
import serial
import subprocess
import LIS3DH #import LIS3DH
import TempHeader1
import time

#############################################################################
accelerometer = LIS3DH.LIS3DH() #Create LIS3DH accelerometer
accel_sensor = TempHeader1.accelerometer_sensor() #Create object for accelerometer_sensor class
tempsensor = TempHeader1.temp_sensor()#Create MCP9808 temp sensor object
alert = TempHeader1.alert() #Create object for alert class
#############################################################################

#############################################################################
movingcar = .1 # max aceleration in m/s^2
lastx = 0 #last known X Coordinates
lasty = 0 #last known Y Coordinates
lastz = 0 #last known Z Coordinates
differencex = 0 # difference between current and last known X Coordinates
differencey = 0 # difference between current and last known Y Coordinates
differencez = 0 # difference between current and last known Z Coordinates
update_time = 1 #check reed sensor every second
start_program = 0
reed_pin = 36
timer = 0 #initiate timer
#timer_speed = 1
timer_speed = input("How fast do you want the each cycle (in seconds)? ")
last_alert = 0
reed_bit = 0 # seat belt check. 1 = unbuckled, 0 = buckled
last_alert = 0
############################################################################

###########################################################################################
BLEstart_time = 0 #TEMPORARY
BLEtimer = BLEstart_time #inital timer value. Timer will be in seconds
BLElast_alert = 0 #time since last alert
danger_rate = 1.9
base_temp = 0
BLEbase_time = 0
temp_rate = 0 #difference between current and last temperature
BLEstart = 0 #will be zero only for timer = 1
BLEonbutton = 40 #onbutton represents parent leaving BLE range
BLEoffbutton= 38 #offbutton represents parent returning to BLE Range
#BLEtimer_speed = 1 #TEMPORARY timer iterates once/second USING timer_speed instead
max = 89 #maximum temperature
BLEfirst_alert= 0 #time of first alert
over = 0 # will allow program to end when EMS is called
#########################################################################################


############################################################################
repeat = 5 #how many times voice call will run
talk_delay = 10 #how long to wait before beginning to talk
car_color = "black"
car_make = "Nissan"
car_model = "Versa"
Longitude = 33.354
Long_Dir = "North"
Lattitude = 56.244
Latt_Dir = "East"
#############################################################################

#############################################################################
GPIO.setmode(GPIO.BOARD)
GPIO.setup(reed_pin, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(BLEonbutton,GPIO.IN, GPIO.PUD_DOWN) 
GPIO.setup(BLEoffbutton,GPIO.IN, GPIO.PUD_DOWN) 
#############################################################################

############################################################################
dev = subprocess.check_output('ls /dev/ttyACM*', shell=True) #find out what name the Arduino is under
print (dev) #display Arduino name (will be shown in bytes)
dev=dev.decode("utf-8") #convert Arduino name from bytes to string
dev=dev.replace("\n","") #get rid of \n

try:
    ser = serial.Serial(dev,9600) # Connect to Arduino's Serial
    print ("Connected to Arduino")
except:
    print ("Arduino not connected")
############################################################################

print("Current Temperature is: %.2f F" %tempsensor.readTempF())      
print("Maximum car temperature is: " + str(max))

def watchTemp (BLEtimer, BLEfirst_alert, BLElast_alert, base_temp, BLEbase_time, BLEstart) :
    i = 0
    left_alone_at = BLEtimer - BLEbase_time
    while True :
        #calculate temperature alert parameters
        temperature = tempsensor.Temperature(base_temp, BLEbase_time, BLEtimer, BLEstart, danger_rate, BLElast_alert, BLEfirst_alert, ser, max)
        alone_time = BLEtimer - left_alone_at
        EMS_time = alone_time - BLEfirst_alert

        #print("i value is : " + str(i)) #TEMPORARY
        print("Child has been alone for : " + str(alone_time) + " seconds") #TEMPORARY
        #print("EMS_time : " + str(EMS_time) + " seconds")
        
        if (temperature['danger_temp_bit'] | temperature['temp_rate_bit']) == 1 : #keep track of when first alert was made
            i = i + 1 #determine if a temperature alert has been sent

            if i == 1 : #only save first alert once
                BLEfirst_alert = temperature['last_alert']
            
            if temperature['danger_temp_bit'] == 1: 
                alert.danger_temp_alert(ser)

            if temperature['temp_rate_bit'] == 1 :
                alert.temp_rate_alert(ser)
 
                
        if ((EMS_time == 4*60) & (i>0)) : #if child's been alone 4 min since first temp alert call EMS
            #alert.parent_EMS_not(ser)
            alert.EMS_call(ser)
            TempHeader1.EMS_caller(repeat, talk_delay, car_color, car_make, car_model, Longitude, Lattitude)
            over = 1
            
        if (alone_time == 60*5) : #if child has been left in car for 5 min send warning text
            alert.warning_alert(ser)
        
        if ((alone_time == 60*9) | ((EMS_time == 3*60) & (i>0))) : #if child has been left in safe temp car for 9 min or parent hasn't returned 3 min after first temp alert, tell parents that EMS is about to be contacted
            alert.EMS_warning_alert(ser)
        
        if (alone_time > 60*10) : #if child has ben left in car for 10 min , tell parents that EMS has been contacted and call EMS
            #alert.parent_EMS_not(ser)
            alert.EMS_call(ser)
            TempHeader1.EMS_caller(repeat, talk_delay, car_color, car_make, car_model, Longitude, Long_Dir, Lattitude, Latt_Dir)
            over = 1
            break
        
        time.sleep(timer_speed) # wait for ___ seconds
        

        if GPIO.input(BLEoffbutton) == 1 : # If offbutton is pushed (parent returns within BLE range)
            print("BLEoffbutton Pressed")
            #Reset first and last temp alerts when parent returns (offbutton is pushed)
            BLElast_alert = 0  
            BLEfirst_alert = 0
            break

        #Update values
        base_temp = temperature['base_temp']
        BLEbase_time = temperature['base_time']
        BLEstart = temperature['start']
        BLElast_alert = temperature['last_alert']
        BLEtimer = BLEtimer + 1
        
    return {"BLEtimer" : BLEtimer, "BLEfirst_alert" : BLEfirst_alert, "BLElast_alert" : BLElast_alert, "base_temp" : base_temp, "BLEbase_time" : BLEbase_time, "BLEstart" : BLEstart}
    
while True:

    print("\r\nCurrent time is: " +str(timer))
    print("Last seat belt alert time: " + str(last_alert))

    moving = accel_sensor.Accelerometer_sensor(ser, timer, GPIO.input(reed_pin), movingcar, last_alert, start_program, lastx, lasty ,lastz)

    #Update values
    last_alert = moving['last_alert']
    start_program = moving['start_program']
    lastx = moving['lastx']
    lasty = moving['lasty']
    lastz = moving['lastz']

    if moving['reed_bit'] == 1 : #if car is moving, text parent
        alert.seat_belt_alert(ser)

    #Moving into temp/BLEcheck
    print("Press BLEonbutton to symbolize parent's leaving child in car.")

    if (GPIO.input(BLEonbutton) == 1): #if ONLY the onbutton is pushed
        print("OnButton Pressed")
        
        alert.warning_alert(ser) #send first warning text
        #print("Time in seconds "+str(BLEtimer))

        #Update values
        checktemp = watchTemp(timer, BLEfirst_alert, BLElast_alert, base_temp, BLEbase_time, BLEstart)
        BLEfirst_alert = checktemp['BLEfirst_alert']
        BLElast_alert = checktemp['BLElast_alert']
        BLEbase_time = checktemp['BLEbase_time']
        base_temp = checktemp['base_temp']
        timer = checktemp['BLEtimer']
        last_alert = 0 # Reset seat belt last #Reset first and last temp alerts when parent returns (offbutton is pushed)
        BLElast_alert = 0  
        BLEfirst_alert = 0
        

    time.sleep(timer_speed)
    timer = timer + 1
    
    if GPIO.input(BLEoffbutton) == 1 : # If offbutton is pushed reset values and send program ending warning
        print("\r\n\r\nProgram offbutton pressed. Hold button for 3 seconds to end program")
        timer = 0
        last_alert = 0
        time.sleep(3)
        
        if GPIO.input(BLEoffbutton) == 1 : # If offbutton is pushed end program
            print("\r\n\r\nGoodbye!\n\n")
            break
          
