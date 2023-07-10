"""
Created on Wed Aug 13 2021
E3631A Triple Output DC Power Supply

code author: M. Jobayer Hossain <jobayer.hossain@hpe.com>
"""
import time
import visa
from util.instrument import GPIBInstrument

rm = visa.ResourceManager()
res = rm.list_resources()
print("Find following resources: " + str(res))
#print("Opening " + res[-1])
#inst = rm.open_resource(res[-1])

class power_supply(GPIBInstrument):
    """
    Wrapper function for E3631A Triple Output DC Power Supply
    """
    def __init__(self,voltage,current,dev_address,go_default = False):
        self.name = "GPIB0::%d::INSTR"%dev_address
        GPIBInstrument.__init__(self, resource_string="GPIB0::%d::INSTR"%dev_address)
        self.timeout = 1000000000
        self.inst.query("*IDN?")
        if go_default == True:
            self.voltage=voltage
            self.current=current
            self.inst.write("INST P6V")                     # Select +6V output
            self.inst.write("VOLT " + str(self.voltage))    # Set output voltage to 2.0 V
            self.inst.write("CURR " + str(self.current))                     # Set output current to 0.5 A

    def output_on(self):
        self.inst.write("OUTP ON")
        print('Output turned on')
        print('Voltage (V):'+str(self.voltage)+', Current (A):' + str(self.current))

    def output_off(self):
        self.inst.write("OUTP OFF")
        print('Output turned off')
    
    def increase_voltage(self, inc):
        self.voltage +=inc
        self.inst.write("VOLT " + str(self.voltage))
        print('Voltage (V):'+str(self.voltage)+', Current (A):' + str(self.current))
        
    def increase_current(self, inc):
        self.current +=inc
        self.inst.write("CURR " + str(self.current))
        print('Voltage (V):'+str(self.voltage)+', Current (A):' + str(self.current))

if __name__=="__main__":
    ps = power_supply(2, 0.5, 11,True) #power_supply(voltage(V), Current (A), GPIB_address, True)
    ps.output_on()
    time.sleep(4)
    ps.increase_voltage(0.5)
    time.sleep(4)
    ps.increase_current(-0.1)
    time.sleep(4)
    ps.output_off()
    print("Code executed successfully")
    last_line = 1