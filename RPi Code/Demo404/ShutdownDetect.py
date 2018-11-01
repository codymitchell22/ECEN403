import RPi.GPIO as GPIO
import os
import time

def ShutdownPressed(arg):
    print("shutting down")
    os.system("sudo shutdown -h now")

GPIO_ButtonShutdown = 32
GPIO.setmode(GPIO.BOARD)


GPIO.setup(GPIO_ButtonShutdown, GPIO.IN, pull_up_down=GPIO.PUD_DOWN) #system shutdown button
GPIO.add_event_detect(GPIO_ButtonShutdown, GPIO.RISING)
GPIO.add_event_callback(GPIO_ButtonShutdown, ShutdownPressed)

while(True):
    #do otherwork
    time.sleep(0.1)
