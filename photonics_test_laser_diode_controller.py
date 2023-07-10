"""
Created on Wed Aug 13 2021
LDC-3724C Laser Diode Controller

code author: M. Jobayer Hossain <jobayer.hossain@hpe.com>
"""

import time
import visa
from util.instrument import GPIBInstrument

rm = visa.ResourceManager()
res = rm.list_resources()
print("Find following resources: " + str(res))


class laser_diode_controller(GPIBInstrument):
    """
    Wrapper function for LDC-3724C Laser Diode Controller
    """
    def __init__(self,dev_address,go_default = False):
        self.name = "GPIB0::%d::INSTR"%dev_address
        GPIBInstrument.__init__(self, resource_string="GPIB0::%d::INSTR"%dev_address)
        self.timeout = 1000000000
        #self.inst.query("LAS:MODE?")
        
    def set_temp(self, temp):
        self.inst.write("TEC:T "+str(temp))
        
    def onoff_temp_output(self, onoff):
        if (onoff==1):
            self.inst.write("TEC:OUT 1")
            print('TEC output enabled')
        elif(onoff==0):
            self.inst.write("TEC:OUT 0")
            print('TEC output disabled')
            
    def measure_temp_value(self):
        t=self.inst.query("TEC:T?")
        print('TEC measured temperature (C): '+str(t))
        
    def set_curr(self, curr):
        self.inst.write("LAS:LDI "+str(curr))
        
    def onoff_curr_output(self, onoff):
        if (onoff==1):
            self.inst.write("LAS:OUT 1")
            print('Current source output enabled')
        elif(onoff==0):
            self.inst.write("LAS:OUT 0")
            print('Current source disabled')        
        
    def measure_curr_value(self):
        c=self.inst.query("LAS:LDI?")
        print('Constant current source measured value (mA): '+str(c))

if __name__=="__main__":
    ldc = laser_diode_controller(1, True)
    
    #TEC Mode
    ldc.set_temp(15)                            #set temperature at certain value, degree C
    ldc.onoff_temp_output(0)                    #1=on, 0=off
    time.sleep(2)                               #Wait for 2s
    ldc.measure_temp_value()                    #TEC measured temperature value
    
    #LAS Mode
    ldc.set_curr(90)                            #set current at certain value, mA
    ldc.onoff_curr_output(0)                    #1=on, 0=off
    time.sleep(4)                               #Wait for 3s
    ldc.measure_curr_value()                    #constant current source measured value
    
    print("Code executed successfully")
    last_line = 1