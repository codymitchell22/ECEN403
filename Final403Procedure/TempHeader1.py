import RPi.GPIO as GPIO
import smbus
import time
from subprocess import call
from LIS3DH import LIS3DH

# Get I2C bus
bus = smbus.SMBus(1)

# I2C Address of the device
MCP9808_DEFAULT_ADDRESS			= 0x18

# MCP9808 Register Pointer
MCP9808_REG_CONFIG				= 0x01 # Configuration Register
MCP9808_REG_UPPER_TEMP			= 0x02 # Alert Temperature Upper Boundary Trip register
MCP9808_REG_LOWER_TEMP			= 0x03 # Alert Temperature Lower Boundary Trip register
MCP9808_REG_CRIT_TEMP			= 0x04 # Critical Temperature Trip register
MCP9808_REG_AMBIENT_TEMP		= 0x05 # Temperature register
MCP9808_REG_MANUF_ID			= 0x06 # Manufacturer ID register
MCP9808_REG_DEVICE_ID			= 0x07 # Device ID/Revision register
MCP9808_REG_RSLTN				= 0x08 # Resolution register

# Configuration register values
MCP9808_REG_CONFIG_DEFAULT		= 0x0000 # Continuous conversion (power-up default)
MCP9808_REG_CONFIG_SHUTDOWN		= 0x0100 # Shutdown
MCP9808_REG_CONFIG_CRITLOCKED	= 0x0080 # Locked, TCRIT register can not be written
MCP9808_REG_CONFIG_WINLOCKED	= 0x0040 # Locked, TUPPER and TLOWER registers can not be written
MCP9808_REG_CONFIG_INTCLR		= 0x0020 # Clear interrupt output
MCP9808_REG_CONFIG_ALERTSTAT	= 0x0010 # Alert output is asserted
MCP9808_REG_CONFIG_ALERTCTRL	= 0x0008 # Alert Output Control bit is enabled
MCP9808_REG_CONFIG_ALERTSEL		= 0x0004 # TA > TCRIT only
MCP9808_REG_CONFIG_ALERTPOL		= 0x0002 # Alert Output Polarity bit active-high
MCP9808_REG_CONFIG_ALERTMODE	= 0x0001 # Interrupt output

# Resolution Register Value
MCP9808_REG_RSLTN_5			= 0x00 # +0.5C
MCP9808_REG_RSLTN_25			= 0x01 # +0.25C
MCP9808_REG_RSLTN_125			= 0x02 # +0.125C
MCP9808_REG_RSLTN_0625			= 0x03 # +0.0625C

def EMS_caller(repeat, delay, car_color, car_make, car_model, Longitude, Long_Dir, Lattitude, Latt_Dir):
    cmd_beg= 'espeak -ven+f3 -g1 -s150'
    cmd_end= ' 2>/dev/null' # To play back the stored .wav file and to dump the std errors to /dev/null
    cmd_out= '--stdout > /home/pi/Desktop/Text.wav ' # To store the voice file

    #text = input("Enter the Text: ")
    intro = "This is the Forget Me Not Child Safety System  A child has been left unattended in a vehicle and needs assistance."
    car_description = "The child is in a " + " ' " + str(car_color) + " ' " + str(car_make) + " ' " + str(car_model) + " ' "
    GPS_Longitude = "at GPS Location " + " ' " + str(Longitude) + " ' " + " degrees " + " ' " + str(Long_Dir) + " ' "
    GPS_Lattitude = " and" + " ' " + str(Lattitude) + " ' " + " degrees " +  " ' " + str(Latt_Dir) + " ' " 
    
    print(intro + car_description + GPS_Longitude + GPS_Lattitude)

    #Replacing ' ' with '_' to identify words in the text entered
    intro = intro.replace(' ', '_')
    car_description = car_description.replace(' ', '_')
    GPS_Longitude = GPS_Longitude.replace(' ', '_')
    GPS_Lattitude = GPS_Lattitude.replace(' ', '_')
    
    time.sleep(delay)
    for num in range(0,repeat) :
        num=num+1
        #Calls the Espeak TTS Engine to read aloud a Text
        call([cmd_beg+cmd_out+intro+cmd_end], shell=True)
        call([cmd_beg+cmd_out+car_description+cmd_end], shell=True)
        call([cmd_beg+cmd_out+GPS_Longitude+cmd_end], shell=True)
        call([cmd_beg+cmd_out+GPS_Lattitude+cmd_end], shell=True)
        time.sleep(1)
    
class alert():
    
    def danger_temp_alert(self, serial):
        print("Car has exceeded max temperature!")
        serial.write(b'1') #green light will turn on and off once
        
    def temp_rate_alert(self, serial):
        print("Car temperature is increasing dangerously fast!")
        serial.write(b'2') #yellow light will turn on and off once
        
    def warning_alert(self, serial):
        print("Child has been left in car alone!")
        serial.write(b'3') #red light will turn on and off once
    
    def EMS_warning_alert(self, serial):
        print("Your child has been left alone in a car after several alerts. Please return to your car. EMS will be contacted in 60 seconds.")
        serial.write(b'4') #yellow and green light will turn on and off once
        
    def EMS_call(self,serial):
        print("Calling EMS")
        serial.write(b'5') #red, yellow, and green light will turn on and off once
    
    def parent_EMS_not(self,serial):
        print("EMS has been contacted")
        serial.write(b'6') #red and green lights will turn on and off once

    def seat_belt_alert(self, serial):
        print("Child is unbuckled in a moving car!")
        serial.write(b'7') #yellow and red lights will turn on and off once
        
class temp_sensor():

    def readTempF(self):
        data = bus.read_i2c_block_data(MCP9808_DEFAULT_ADDRESS, MCP9808_REG_AMBIENT_TEMP, 2)
		
	# Convert the data to 13-bits
        TempC = ((data[0] & 0x1F) * 256) + data[1]
        if TempC > 4095 :
            TempC -= 8192
        TempC = TempC * 0.0625
        TempF = TempC * 1.8 + 32
        return TempF
    
    def calc_rate(self, temp, base_temp, base_time, timer, start):
        
        if start== 0: #check if program just started
            start = 1
            last_temp = temp #ignore initial last_temp value
            base_temp = temp #set base temp. Will be updated every minute
            base_time = timer
            #print("calc rate base_temp : " + str(base_temp))
            #print("calc rate base_time : " + str(base_time))
            #print("New last_temp value: " + str(last_temp))
               
        temp_rate = temp - base_temp # calculate how fast temperature has changed in last minute
        #print("Base temperature was " + str(base_temp) + " at the " + str(base_time) + " second mark.")
        print("Temperature change within the last minute : " + str(temp_rate))
        
        if (timer-base_time) > 59 : #Check if minute has passed
            base_time=timer #update base time every minute
            base_temp=temp #update base temp every minute
            
        return {"temp_rate" : temp_rate, "base_temp" : base_temp, "base_time" : base_time, "start" :start}

    def Temperature(self, base_temp, base_time, timer, start, danger_rate, last_alert, first_alert, serial, max):

        print("\r\nCurrent time is: " +str(timer))
        print("First temperature alert time: " +str(first_alert))
        print("Last temperature alert time: " + str(last_alert))

        temp_rate_bit = 0
        danger_temp_bit = 0
        temp = temp_sensor.readTempF(self) #Read temperature in F

        #print ("Max temperature : " + str(max))
        print ("Current Temperature in Fahrenheit : %.2f F"%(temp)) #Display temperature
        
        if str(temp) > str(max): #check if current temp is higher than defined max temp
            print("Dangerously hot temperatures!")
            if last_alert == 0 :
                last_alert=timer
                danger_temp_bit = 1 #trigger danger_temp_alert() SMS warning
                
            if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
                last_alert=timer
                danger_temp_bit = 1 #trigger danger_temp_alert() SMS warning

        rate = temp_sensor.calc_rate(self, temp, base_temp, base_time, timer, start) #Calculate change in temperature
        start = rate['start']
        base_time = rate['base_time']
        base_temp = rate['base_temp']
    
        if rate['temp_rate'] > danger_rate : #Check if temperature is rising too quickly
            #print("Dangerous increase in temperature!")
        
            if last_alert == 0 :
                last_alert=timer
                temp_rate_bit = 1 #trigger temp_rate_alert() SMS warning
                
            if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
                last_alert=timer
                temp_rate_bit = 1 #trigger temp_rate_alert() SMS warning
        
        return {"base_temp" : base_temp, "base_time" : base_time, "start" : start, "last_alert" : last_alert, "temp_rate_bit" : temp_rate_bit, "danger_temp_bit" : danger_temp_bit}
        
class accelerometer_sensor() :

    def rateAccel(self, movingcar, currentx, currenty, currentz, lastx, lasty, lastz):
        differencex = currentx - lastx
        differencey = currenty - lasty
        differencez = currentz - lastz
        #print("\rdiffX: %.6f\tdiffY: %.6f\tdiffZ: %.6f \t m/s^2" % (differencex, differencey, differencez))

        if (abs(differencex)>movingcar) | (abs(differencey)>movingcar) | (abs(differencez)>movingcar) :
            print("You're moving!")
            return 1

        else :
            print("Car isn't moving.")
            return 0

    def Accelerometer_sensor(self, serial, timer, reed_input, movingcar, last_alert, start_program, lastx, lasty, lastz):
        Accelerometer = LIS3DH()
        reed_bit = 0

        x = Accelerometer.getX()
        y = Accelerometer.getY()
        z = Accelerometer.getZ()
        
        if start_program == 0 : #prevents false acceleration alerts
            i = 0
            start_program = 1
            lastx = x
            lasty = y
            lastz = z
            #print("\rnewlastX: %.6f\tnewlastY: %.6f\tnewlastZ: %.6f \t m/s^2" % (x, y, z))
    
        #  Display results (acceleration is measured in m/s^2)
        print("\rX: %.6f\tY: %.6f\tZ: %.6f \td m/s^2" % (x, y, z))
        #print("\rlastX: %.6f\tlastY: %.6f\tlastZ: %.6f \t m/s^2" % (lastx, lasty, lastz))

        if reed_input == 1 : #check if child is buckled
            print("Seat belt buckled")
        else :
            print("Seat unbuckled")
                
        if accelerometer_sensor.rateAccel(self, movingcar, x, y, z, lastx, lasty, lastz) == 1 : #if car is moving
            if reed_input == 0 : #if seat is unbuckled update last_alert
                if last_alert == 0 : #If parent hasn't been notified
                    last_alert = timer #Update last_alert time
                    reed_bit = 1 #trigger danger_temp_alert() SMS warning
                    
                if (timer-last_alert) > 60*5 : #If it's been more than 5 minutes since the last alert send another
                    last_alert = timer #Update last_alert time
                    reed_bit = 1 #trigger danger_temp_alert() SMS warning
            
                #start_program = 0 #reset program values
                

        #Update coordinate values
        lastx = x
        lasty = y
        lastz = z
        

        return {"reed_bit" : reed_bit, "last_alert" : last_alert, "start_program" : start_program, "lastx" : lastx, "lasty" : lasty, "lastz" : lastz}

