from temp_header import temp_sensor
import time
tempsensor = temp_sensor()

while True:
	temp = tempsensor.readTempF()
	print ("Temperature in Fahrenheit : %.2f F"%(temp['f']))
	time.sleep(1)
