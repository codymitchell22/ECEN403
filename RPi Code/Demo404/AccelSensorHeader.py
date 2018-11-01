import RPi.GPIO as GPIO
import smbus
import time
from subprocess import call
from LIS3DH import LIS3DH

class accelerometer_sensor() :

    def rateAccel(self, movingcar, currentx, currenty, currentz, lastx, lasty, lastz):
        differencex = currentx - lastx
        differencey = currenty - lasty
        differencez = currentz - lastz
        
        if (abs(differencex)>movingcar) | (abs(differencey)>movingcar) | (abs(differencez)>movingcar) :
            print("You're moving!")
            return 1

        else :
            print("Car isn't moving.")
            return 0

    def Accelerometer_sensor(self, timer, reed_input, movingcar, last_alert, start_program, lastx, lasty, lastz):
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
            
        if reed_input == 1 : #check if child is buckled
            print("Seat belt buckled")
        else :
            print("Seat unbuckled")
                
        if accelerometer_sensor.rateAccel(self, movingcar, x, y, z, lastx, lasty, lastz) == 1 : #if car is moving
            if reed_input == 0 : #if seat is unbuckled update last_alert
                if last_alert == 0 : #If parent hasn't been notified
                    last_alert = timer #Update last_alert time
                    reed_bit = 1 #trigger seat_belt_alert() SMS warning
                    
                if (timer-last_alert) > 60*5 : #If it's been more than 5 minutes since the last alert send another
                    last_alert = timer #Update last_alert time
                    reed_bit = 1 #trigger seat_belt_alert() SMS warning

        #Update coordinate values
        lastx = x
        lasty = y
        lastz = z

        return {"reed_bit" : reed_bit, "last_alert" : last_alert, "start_program" : start_program, "lastx" : lastx, "lasty" : lasty, "lastz" : lastz}

