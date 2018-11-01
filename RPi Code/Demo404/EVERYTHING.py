#!/usr/bin/python

import thread
import RPi.GPIO as GPIO
import subprocess
import GSMheader
import AccelSensorHeader
import LIS3DH
import TempHeader1
import time
import bluetooth
import smbus
import serial
import pygame
from subprocess import call
from threading import Thread
from Queue import Queue
import threading
import random

#CREATE OBJECTS FROM HEADER CLASSES##########################################
accelerometer = LIS3DH.LIS3DH() #Create LIS3DH accelerometer
accel_sensor = AccelSensorHeader.accelerometer_sensor() #Create object for accelerometer_sensor class
tempsensor = TempHeader1.temp_sensor()#Create MCP9808 temp sensor object
#############################################################################

# INITIAL ACCELEROMETER DATA###################################################
movingcar = .1 # max aceleration in m/s^2
lastx = 0 #last known X Coordinates
lasty = 0 #last known Y Coordinates
lastz = 0 #last known Z Coordinates
last_alert = 0
############################################################################

###########################################################################################
BLEstart_time = 0 #TEMPORARY
BLElast_alert = 0 #time since last alert
danger_rate = 1.9
base_temp = 0
BLEbase_time = 0
temp_rate = 0 #difference between current and last temperature
BLEstart = 0 #will be zero only for timer = 1
#BLEtimer_speed = 1 #TEMPORARY timer iterates once/second USING timer_speed instead
maxtemp = 89 #maximum temperature
BLEfirst_alert= 0 #time of first alert
over = 0 # will allow program to end when EMS is called
#########################################################################################

############################################################################
EMSnum = "8327978415"
phonenum = "8304809421"
backupnum = "\r"
car_color = "\r"
car_type = "\r"
License_plate = "\r"
Longitude = "\r"
Latitude = "\r"
connection_bit = "\r"
running = False
#############################################################################

# SETUP GPIO PINS############################################################################
reed_pin = 36
Speaker = 38
GSMpower = 11
GSMreset = 12
GPIO.setmode(GPIO.BOARD)
GPIO.setup(reed_pin, GPIO.IN, GPIO.PUD_DOWN)
GPIO.setup(Speaker,GPIO.OUT)
GPIO.setup(GSMreset,GPIO.OUT)
GPIO.setup(GSMpower,GPIO.OUT)
GPIO.output(GSMpower,1) #Turn on GSM
GPIO.output(GSMreset,1) #Turn off GSM
GPIO.output(GSMreset,0) #Turn on GSM
GPIO.output(Speaker,0) #Initialize Speaker as off
##############################################################################

# INITIAL TIMER DATA #########################################################
start_program = 0
global timer
timer = 0 #initiate timer
timer_speed = .5
##############################################################################
   
def seat_belt_alert( textnumber):
    message = "Your child is unbuckled in a moving car!"
    GSMheader.StayorGoSMS(textnumber,message)

def warning_alert(textnumber):
    message = "Child has been left in car alone!"
    GSMheader.StayorGoSMS(textnumber,message)

def danger_temp_alert(textnumber):
    message = "Your child has been left alone in a hot car. Return to your car immediately!"
    GSMheader.StayorGoSMS(textnumber,message)
    
def temp_rate_alert(textnumber):
    message = "Your child has been left in the car, and the temperature is rising rapidly. Return to your car immediately!"
    GSMheader.StayorGoSMS(textnumber,message)
    
def EMS_warning_alert(textnumber):
    message = "Your child is still alone in a car after several alerts. Please return to your car immediately. EMS will be contacted in 60 seconds."
    GSMheader.StayorGoSMS(textnumber,message)
    
def parent_EMS_not(textnumber):
    message = "EMS has been contacted. Your child has been left in a car alone for an extended period of time. Please return to your car immediately!"
    GSMheader.StayorGoSMS(textnumber,message)


def EMS_call(callnumber,car_color, car_type, License_plate, Longitude, Latitude):
    GSMheader.FlushSerial()
    GSMerror = 0 # Keeps track of how many times GSM has thrown an error
    success = GSMheader.GSMcall(callnumber,car_color, car_type, License_plate, Longitude, Latitude) #Call and let us know if attempt was succesfull
    while True:
        if  success == 1:
            print("SMS successful. Total GSM errors: " + str(GSMerror))
            return GSMerror #Send updated GSM error count to Main function
            break #If Message was sent successully, continue with Main Code
        else:
            GSMheader.FlushSerial()
            GSMerror = GSMheader.GSMerrorfunc(GSMerror) #Update the GSMerror count
            success = GSMheader.GSMcall(callnumber,car_color, car_type, License_plate, Longitude, Latitude) #Resend text
      
def watchTemp (phonenum,backupnum,car_color,car_type,License_plate,Longitude,Latitude, BLEfirst_alert, BLElast_alert, base_temp, BLEbase_time, BLEstart) :
    global connection_bit
    global timer
    active = threading.active_count() #Count active threads
    i = 0
    left_alone_at = timer - BLEbase_time
    
    if active <= 3:
        warningSMS = threading.Thread(target = warning_alert ,args = (phonenum,))#send first warning text
        warningSMS.start()
        
    while True :
        active = threading.active_count() #Count active threads
        print("Active Threads: " + str(active)) #If there are more than 3 active threads, the GSM is busy.
        print("Phone Disconnected")
        print("Primary Phone: " + str(phonenum))
        print("Backup Phone: " + str(backupnum))
        print("Car Color: " + str(car_color))
        print("Car Type: " + str(car_type))
        print("License Plate: " + str(License_plate))
        print("Last Known GPS Longitude: " + str(Longitude))
        print("Last Known GPS Latitude: " + str(Latitude))
        
        #calculate temperature alert parameters
        temperature = tempsensor.Temperature(base_temp, BLEbase_time, timer, BLEstart, danger_rate, BLElast_alert, BLEfirst_alert, maxtemp)
        alone_time = timer - left_alone_at
        EMS_time = alone_time - BLEfirst_alert
        
        print("Child has been alone for : " + str(alone_time) + " seconds") #TEMPORARY
        
        if (temperature['danger_temp_bit'] | temperature['temp_rate_bit']) == 1 : #keep track of when first alert was made
            i = i + 1 #determine if a temperature alert has been sent

            if i == 1 : #only save time of first temperature alert once
                BLEfirst_alert = temperature['last_alert'] #Save time of first temperature alert. Call for help in 4 min
            
            if temperature['danger_temp_bit'] == 1 & (active<=3): 
                dangertempSMS = threading.Thread(target = danger_temp_alert,args = (testnum,)) #if car is at a dangerous temperature, send text.
                dangertempSMS.start()
            if temperature['temp_rate_bit'] == 1 & (active<=3):
                temprateSMS = threading.Thread(target = temp_rate_alert ,args = (testnum,)) #if car temp in increasing rapidly, send text.
                temprateSMS.start()
 
        if (((EMS_time == 4*60) & (i>0)) & (active<=3)): #if child's been alone 4 min since first temp alert call EMS
            EMStempcalling = threading.Thread(target = EMS_call ,args = (EMSnum,car_color, car_type, License_plate, Longitude, Latitude))
            EMStempcalling.start()
            break
            
        if (alone_time == 60*5) & (active<=3): #if child has been left in car for 5 min send warning text
            warningSMS2 = threading.Thread(target = warning_alert,args = (phonenum,))
            warningSMS2.start()
        
        if (((alone_time == 60*9) | ((EMS_time == 3*60) & (i>0))) & (active<=3)) : #if child has been left in safe temp car for 9 min or parent hasn't returned 3 min after first temp alert, tell parents that EMS is about to be contacted
            EMSwarningSMS = threading.Thread(target = EMS_warning_alert,args = (phonenum,))
            EMSwarningSMS.start()
        
        if (alone_time == 60*10) & (active<=3): #if child has ben left in car for 10 min , tell parents that EMS has been contacted and call EMS
            EMScalling = threading.Thread(target = EMS_call ,args = (EMSnum,car_color, car_type, License_plate, Longitude, Latitude))
            EMScalling.start()
            left_alone_at = timer
            break
            
        
        time.sleep(timer_speed) # wait for 1 second
        
        if connection_bit == "1" : # System begins recieving parent GPS Location, go back to checking if child is unbuckled in moving car
            print("App Reconnected")
            #Reset first and last temp alerts when parent returns (offbutton is pushed)
            BLEbase_time = 0
            BLElast_alert = 0  
            BLEfirst_alert = 0
            break

        #Update values
        base_temp = temperature['base_temp']
        BLEbase_time = temperature['base_time']
        BLEstart = temperature['start']
        BLElast_alert = temperature['last_alert']
        timer = timer + 1
        
    return {"BLEfirst_alert" : BLEfirst_alert, "BLElast_alert" : BLElast_alert, "base_temp" : base_temp, "BLEbase_time" : BLEbase_time, "BLEstart" : BLEstart}

def checkMovement(last_alert, start_program, lastx, lasty, lastz, BLEfirst_alert, BLElast_alert, BLEbase_time, base_temp):
    try:
        while (True):
            
            global phonenum
            global backupnum
            global car_color
            global car_type
            global License_plate
            global Longitude
            global Latitude
            global connection_bit
            global timer
            global running
            
            print("\r\nCurrent time is: " +str(timer))
            print("Primary Phone: " + str(phonenum))
            print("Backup Phone: " + str(backupnum))
            print("Car Color: " + str(car_color))
            print("Car Type: " + str(car_type))
            print("License Plate: " + str(License_plate))
            print("Last Known GPS Longitude: " + str(Longitude))
            print("Last Known GPS Latitude: " + str(Latitude))
            print("Last seat belt alert time: " + str(last_alert))
            print("Phone is connected")
    
            moving = accel_sensor.Accelerometer_sensor(timer, GPIO.input(reed_pin), movingcar, last_alert, start_program, lastx, lasty ,lastz)

            #Update accerometer/reed sensor/ alert values
            last_alert = moving['last_alert']
            start_program = moving['start_program']
            lastx = moving['lastx']
            lasty = moving['lasty']
            lastz = moving['lastz']

            if moving['reed_bit'] == 1 : #if child unbuckled in moving car, text parent
                GPIO.output(Speaker,1) #Turn on Speaker
            else: GPIO.output(Speaker,0) #Turn off Speaker

            if connection_bit == "0" : #Disconnected from App begin Temp/Timer alert procedure
                          
                #Update values
                checktemp = watchTemp(phonenum,backupnum,car_color,car_type,License_plate,Longitude,Latitude, BLEfirst_alert, BLElast_alert, base_temp, BLEbase_time, BLEstart)
                BLEfirst_alert = checktemp['BLEfirst_alert']
                BLElast_alert = checktemp['BLElast_alert']
                BLEbase_time = checktemp['BLEbase_time']
                base_temp = checktemp['base_temp']
                last_alert = 0 # Reset seat belt last #Reset first and last temp alerts when parent returns (offbutton is pushed)
                BLElast_alert = 0  
                BLEfirst_alert = 0
            time.sleep(timer_speed)
            timer = timer + 1
    
    except StopIteration as err:
        print("GSM has thrown three errors. Check GSM. Exiting Main Procedure Code.")

def assigndata(data):
    global phonenum
    global backupnum
    global car_color
    global car_type
    global License_plate
    global Longitude
    global Latitude
    global connection_bit
    
    testsite_array = []
    for line in data:
        if line != "\n":
            testsite_array.append(line)
            if testsite_array[0] == "P" and testsite_array[-1] == '\r':
                phonenum = ''.join(testsite_array[1:-1]) #Combine array into string
 
            if testsite_array[0] == "B" and testsite_array[-1] == '\r':
                backupnum = ''.join(testsite_array[1:-1])
                
            if testsite_array[0] == "C" and testsite_array[-1] == '\r':
                car_color = ''.join(testsite_array[1:-1])
               
            if testsite_array[0] == "T" and testsite_array[-1] == '\r':
                car_type = ''.join(testsite_array[1:-1])
              
            if testsite_array[0] == "H" and testsite_array[-1] == '\r':
                License_plate = ''.join(testsite_array[1:-1])
              
            if testsite_array[0] == "O" and testsite_array[-1] == '\r':
                Longitude = ''.join(testsite_array[1:-1])
              
            if testsite_array[0] == "A" and testsite_array[-1] == '\r':
                Latitude = ''.join(testsite_array[1:-1])
                
            if testsite_array[0] == "R" and testsite_array[-1] == '\r':
                connection_bit = ''.join(testsite_array[1:-1])
        else:
                testsite_array = []
                     
def connected2App():  
    global connection_bit
    while (True):
        server_sock=bluetooth.BluetoothSocket(bluetooth.RFCOMM)
        port = 1
        server_sock.bind(("",port))
        server_sock.listen(1)
        client_sock,address = server_sock.accept() #recieve phone's MAC
       
        if (address == ('50:77:05:A7:B3:99', 1)): #if connected to phone
            print"Accepted connection from ", address

            while (True):
                try:
                    connection_bit = "1"
                    assigndata(client_sock.recv(1024))
                    
                except:
                    print "App has disconnected"
                    address = 0 #reset address
                    connection_bit = "0"
                    break #break loop begin checking if phone has reconnected
        
    client_sock.close()
    server_sock.close()

        
###############START OF PROGRAM############################################
print("Current Temperature is: %.2f F" %tempsensor.readTempF())      
print("Maximum car temperature is: " + str(maxtemp))
# Create two threads as follows

try:
    thread1 = threading.Thread( target=checkMovement,name = 'Movement Check', args= (last_alert, start_program, lastx, lasty, lastz, BLEfirst_alert, BLElast_alert, BLEbase_time, base_temp))
    thread2 = threading.Thread( target=connected2App,name = 'Bluetooth', args=() )

    thread1.start()
    thread2.start()
    thread1.join()
    thread2.join()

except:
    print "Error: unable to start thread"

while 1: #Keep running threads
    pass
