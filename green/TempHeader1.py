import smbus
import time

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
    
class temp_sensor():
       
    class alert():
        def danger_temp_alert(self, timer,serial):
            last_alert = timer
            print("Dangerous temperature! \n")
            serial.write(b'1') #green light will turn on and off once
            return last_alert
        
        def temp_rate_alert(self, timer, serial):
            last_alert = timer
            print("Temperature rising dangerously fast! \n")
            serial.write(b'2') #yellow light will turn on and off once
            return last_alert
    
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
            #print("New last_temp value: " + str(last_temp))
               
        temp_rate = temp - base_temp # calculate how fast temperature has changed in last minute
        print("Base temperature was " + str(base_temp) + " at the " + str(base_time) + " second mark.")
        #print("Temperature change within the last minute : " + str(temp_rate))
        
        if (timer-base_time) > 59 : #Check if minute has passed
            base_time=timer #update base time every minute
            base_temp=temp
            
        return {"temp_rate" : temp_rate, "base_temp" : base_temp, "base_time" : base_time, "start" :start}

    def Temperature(self, base_temp, base_time, timer, start, danger_rate, last_alert, serial):
        temp = temp_sensor.readTempF(self) #Read temperature in F
        alert = temp_sensor.alert() #Create alerts object 
        print ("Current Temperature in Fahrenheit : %.2f F"%(temp)) #Display temperature
        if str(temp) > str(max): #check if current temp is higher than defined max temp
            if last_alert == 0 :
                last_alert=alert.danger_temp_alert(timer,serial) #trigger SMS warning
                
            if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
                last_alert=alert.danger_temp_alert(timer,serial) #trigger SMS warning

        rate = temp_sensor.calc_rate(self, temp, base_temp, base_time, timer, start) #Calculate change in temperature
        #Consider getting rid of last_temp value. Not using it right now.
        start = rate['start']
        base_time = rate['base_time']
        base_temp = rate['base_temp']
    
        if rate['temp_rate'] > danger_rate : #Check if temperature is rising too quickly
            print("Danger! \n\n")
        
            if last_alert == 0 :
                last_alert=alert.temp_rate_alert(timer, serial) #trigger SMS warning
        
            if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
                last_alert=alert.temp_rate_alert(timer,serial) #trigger SMS warning
        
        else : print ("Safe \n\n")
        return {"base_temp" : base_temp, "base_time" : base_time, "start" : start, "last_alert" : last_alert}
        #last_temp=temp # Update last_temp value before getting new measurement
    
    
    
