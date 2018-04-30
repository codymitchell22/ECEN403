#from TempHeader import temp_sensor
import time
import serial
import time
import subprocess
dev = subprocess.check_output('ls /dev/ttyACM*', shell=True) #find out what name the Arduino is under
print (dev) #display Arduino name (will be shown in bytes)
dev=dev.decode("utf-8") #convert Arduino name from bytes to string
dev=dev.replace("\n","") #get ride of \n
try:
    ser = serial.Serial(dev,9600) # Connect to Arduino's Serial
    print ("Connected to Arduino")
except:
    print ("Arduino not connected")

#tempsensor = temp_sensor()#Creat MCP9808 temp sensor object

max = input("Choose a maximum temperature \n")

while True:
    #temp = tempsensor.readTempF() #Read temperature in F
    temp=input("Choose the temp\n")
    #print ("Temperature in Fahrenheit : %.2f F"%(temp['f'])) #Display temperature
    print ("Temperature in Fahrenheit : "+ str(temp))
    
    if int(temp) > int(max) :
        print("Dangerous temperature!")
        ser.write(b'1')
        print(ser.readline())
            
    time.sleep(1)
