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

timer = 0 #inital timer value. Timer will be in seconds
last_alert = 0 #time since last alert
danger_rate = 1.9
last_temp = 0 # keep track of last temp measurement
base_temp = 0
base_time = 0
temp_rate = 0 #difference between current and last temperature
start = 0 #will be zero only for timer = 1

print("Current Temperature is: %.2f F" %tempsensor.readTempF())      
#max = input("Choose a maximum temperature \n")
max = 89 #auto
print("Maximum car temperature is: " + str(max))
#primarynum = input("Enter parent's contact number. \n")

primarynum = 8327978415 #auto
print("Primary contact number is: " +str(primarynum) + "\n\n")
primarynum = str(primarynum)
primarynum = primarynum.encode("utf-8")



while True:
    timer = timer + 1
    temp = tempsensor.readTempF() #Read temperature in F
    
    print ("Current time: " + str(timer))
    print ("Time of last alert : " + str(last_alert))
    print ("Current Temperature in Fahrenheit : %.2f F"%(temp)) #Display temperature
    print ("Last Temperature in Fahrenheit : " + str(last_temp) + " F")
    #print ("Maximum Temperature set for: " + str(max))
    #print ("Start is set to : " + str(start))
    if str(temp) > str(max): #check if current temp is higher than defined max temp
        if last_alert == 0 :
            last_alert=alert.danger_temp_alert(timer,ser) #trigger SMS warning
        
        if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
            last_alert=alert.danger_temp_alert(timer,ser) #trigger SMS warning
    
    rate = tempsensor.calc_rate(last_temp, temp, base_temp, base_time, timer, start) #Calculate change in temperature
    #Consider getting rid of last_temp value. Not using it right now.
    start = rate['start'] 
    base_time = rate['base_time']
    base_temp = rate['base_temp']
    
    if rate['temp_rate'] > danger_rate : #Check if temperature is rising too quickly
        print("Danger! \n\n")
        if last_alert == 0 :
            last_alert=alert.temp_rate_alert(timer,ser) #trigger SMS warning
        
        if (timer-last_alert) > 60 : #If it's been more than a minute since the last alert send another
            last_alert=alert.temp_rate_alert(timer,ser) #trigger SMS warning
            
    else : print ("Safe \n\n")
    
    last_temp=temp # Update last_temp value before getting new measurement
    time.sleep(1) #wait 1 second
    
    

