import TempHeader # import temp_sensor
import time
import serial
import time
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

tempsensor = TempHeader.temp_sensor()#Create MCP9808 temp sensor object
alert = TempHeader.alerts() #Create alerts object

print("Current Temperature is: %.2f F" %tempsensor.readTempF())      
max = input("Choose a maximum temperature \n")
#max = 89 #auto
print("Maximum car temperature is: " + str(max))
#primarynum = input("Enter parent's contact number. \n")
primarynum = 8327978415 #auto
print("Primary contact number is: " +str(primarynum))
primarynum = str(primarynum)
primarynum = primarynum.encode("utf-8")
timer = 0
last_alert = 0 #time since last alert 

while True:
    timer = timer + 1
    temp = tempsensor.readTempF() #Read temperature in F
    
    print ("Current time: " + str(timer))
    print ("Temperature in Fahrenheit : %.2f F"%(temp)) #Display temperature
    print ("Maximum Temperature set for: " + str(max))
    print ("Time of last alert : " + str(last_alert) + "\n")
    
    if (str(temp) > str(max)): #check if current temp is higher than defined max temp
        if last_alert == 0 :
            last_alert=alert.danger_temp_alert(timer,ser)
        
        if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
            last_alert=alert.danger_temp_alert(timer,ser)
        
    time.sleep(1) #wait 1 second
    
    
