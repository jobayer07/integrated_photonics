import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import PySimpleGUI as sg
import numpy as np
import math
import os
import csv
import time

from matplotlib .ticker import AutoMinorLocator
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg

#from gpib_control.keithleyP3 import Keithley2400
#from gpib_control.DAQ_ControlP3 import DAQ_AI_Control
#from gpib_control.santec_ecdlP3 import SantecTSL510_OBand
#from gpib_control.power_meterP3 import NewportPowerMeter2936C

#------------------------------------------GUI Starts here-----------------------------------------

sg.theme('darkgreen')
layout = [  #[sg.Text("GPIB"), sg.InputCombo([20, 21, 22, 23, 24, 25, 26], default_value='24', size=(4,1), key='gpib_number'), sg.Button('Initiate', border_width=5, size=(4,1), button_color='orangered', mouseover_colors=('yellow','black')), sg.Text("Status"), sg.Output(background_color='white', size=(50,1))],
            [sg.Text("GPIB Address"), sg.Input(size=(5,1)), sg.Button('Initiate', border_width=5, size=(4,1), button_color='orangered', mouseover_colors=('yellow','black')), sg.Text("Status"), sg.Output(background_color='white', size=(50,1))],            
            [sg.Text(" ")],
            [sg.Text("Laser Sweep:"), sg.Text("Align Wavelength (nm)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Laser Power (dBm)"), sg.Input(background_color='white', size=(5,1)), sg.Button('Laser Sweep', button_color='royalblue'), sg.Button('Save Data', button_color='royalblue')],
            [sg.Text("                      "), sg.Text("Start Wavelength (nm)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Stop Wavelength (nm)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Resolution (nm)"), sg.Input(background_color='white', size=(5,1))],
            [sg.Text("                          "), sg.Graph((200, 200), (-10, -10), (10, 10), background_color='white', border_width=0, key='power_graph')],
            [sg.Text("Keithley Sweep:"), sg.Text("Start Voltage (v)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Stop Voltage (v)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Step (V)"), sg.Input(background_color='white', size=(5,1)), sg.Button('Voltage Sweep', button_color='royalblue')],
            [sg.Text("                         "), sg.Text("Start Current (A)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Stop Current (A)"), sg.Input(background_color='white', size=(5,1)), sg.Text("Step (A)"), sg.Input(background_color='white', size=(5,1)), sg.Button('Current Sweep', button_color='royalblue')],
            [sg.Text("                          "), sg.Graph((200, 200), (-10, -10), (10, 10), background_color='white', border_width=0, key='iv_graph'), sg.Button('Save Sweep Data', button_color='royalblue')],            
            [sg.Text(" ")],
            [sg.Text(" ")],
            [sg.Text(" ")],
            [sg.Text("Copyright: Large Scale Integrated Photonics Labs, Hewlett Packard Enterprise, Milpitas, CA 95035, USA")]]

#print(sg.Window.get_screen_size())
#w, h = sg.Window.get_screen_size()

window = sg.Window('Automated Test GUI', layout, location=(0,0), size=(1300,1440), margins=(5, 5))#, font='Helvetica 16')     
power_graph = window['power_graph']
iv_graph = window['iv_graph']  


def draw_figure(canvas, x, y):
    figure, ax = plt.subplots(figsize=(2,2))  #figsize=(2 inch,2inch)
    line, = ax.plot(V, I, '.k')
    ax.set_title('I-V Curve', loc='center', fontsize=10, color='blue')
    plt.xlabel('Voltage (V)', fontsize=8, color='blue')
    plt.ylabel('Current (A)', fontsize=8, color='blue')
    #plt.xticks()
    plt.xticks(fontsize=6)
    plt.yticks(fontsize=6)
    plt.tight_layout()
    plt.grid(True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='major', direction='in', color='k')
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='minor', direction='in', color='k')
    
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="right", fill="both", expand=1)
    return figure_canvas_agg


def laser_sweep(start, stop, resolution):
    powerMeter1 = NewportPowerMeter2936C(channel = 1,resource_string=u'ASRL6::INSTR',
            simulate = False,serial_echo=False)
    
    #powerMeter2 = NewportPowerMeter2936C(channel = 1,resource_string=u'ASRL7::INSTR',
     #                                   simulate = False,serial_echo=True)
    
    laser = SantecTSL510_OBand(dev_address=11,simulate = False)
    
    laser.wavelength = 1309.0
    laser.wait_until_complete()
    laser.power = 0.000          # Laser power in dBm
    laser.sweep_start = start    # Sweep start wavelength #1260
    laser.sweep_stop = stop      # Sweep stop wavelength #1360
    laser.sweep_speed = 80       # nm/s
    resolution = resolution      # Desired sweep resolution #0.002        
    laser.ld_on()
    
    """ Relevant parameters for the DAQ for laser sweep! """
    
    Nsamples = int((laser.sweep_stop - laser.sweep_start)/resolution)
    wavelength = np.linspace(laser.sweep_start,laser.sweep_stop,Nsamples)
    sweep_time = (laser.sweep_stop - laser.sweep_start)/laser.sweep_speed
    clock_rate = float(Nsamples/sweep_time)
    
    for i in range(1):
        print ('Sweep Number: {}'.format(i))
        DAQ_task = DAQ_AI_Control(samples_per_channel = Nsamples, 
            analog_in_addr='Dev2/ai0', 
            terminal = 'diff',
            min_val = 0.0,
            max_val = 1.0,
            #clocksource = clocksource,
            clock_rate = clock_rate,
            active_edge = 'rising',
            sample_mode = 'finite',
            trigger_in_addr='/Dev2/PFI0', 
            buffer_size=50000, 
            simulate=False)
        
        DAQ_task.create_voltage_channel(phys_channel='Dev2/ai3',
                                        terminal = 'diff', 
                min_val=0.0, 
                max_val=1.0)
    
    
        DAQ_task.start()
        laser.sweep(foreground=True)
        laser.wait_until_complete()
        data = DAQ_task.read(int(Nsamples), fill_mode='group_by_channel')
        data = np.squeeze(data)
        #data_b = data[1]
        data = data[0]
        
        DAQ_task.stop()
        del DAQ_task
        
        powerMeter1.set_channel('A')
        pdRange = -4.873
        linRange = 10**(pdRange/10)
        
        linearData = data*linRange
        
        dbdata = [10*np.log10(abs(d)) for d in linearData]
        #plt.plot(wavelength,dbdata)
        #plt.show()    
    return wavelength, dbdata

def generate_output_file(wl, power):
    i=1
    data_dir='C:\lsip-measurement-pycontrol\Jet2\test'
    data_with_wl=np.zeros((power.shape[0],2))
    data_with_wl[:,0]=wl
    data_with_wl[:,1]=power
    #data_with_wl[:,1]=dbdata_b
    np.savetxt(data_dir.format(i)+".csv",data_with_wl,delimiter=',')    
    return  

def draw_power_vs_wavelength_figure(canvas, x, y):
    figure, ax = plt.subplots(figsize=(2,2))  #figsize=(2 inch,2inch) dpi=50
    line, = ax.plot(wavelength, power, '-k')
    ax.set_title('Power-Wavelength Curve', loc='center', fontsize=8, color='blue')
    plt.xlabel('Wavelength (nm)', fontsize=6, color='blue')
    plt.ylabel('Power (dBm)', fontsize=6, color='blue')
    #plt.xticks()
    #plt.xlabel(xlabel, fontdict=None, labelpad=None, loc=None)
    plt.xticks(fontsize=6)
    plt.yticks(fontsize=6)
    #ax.yaxis.set_label_coords(0, 0)
    plt.tight_layout()
    plt.grid(True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='major', direction='in', color='k')
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='minor', direction='in', color='k')
    #plt.show()
    
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    #figure_canvas_agg.get_tk_widget().pack_forget()
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="right", fill="both", expand=1)

    return figure_canvas_agg

def draw_power_vs_wavelength_dataframe(canvas, x, y):
    figure, ax = plt.subplots(figsize=(2,2))  #figsize=(2 inch,2inch) dpi=50
    line, = ax.plot(wavelength, power, '-k')
    ax.set_title('Power-Wavelength Curve', loc='center', fontsize=8, color='blue')
    plt.xlabel('Wavelength (nm)', fontsize=6, color='blue')
    plt.ylabel('Power (dBm)', fontsize=6, color='blue')
    #plt.xticks()
    #plt.xlabel(xlabel, fontdict=None, labelpad=None, loc=None)
    plt.xticks(fontsize=6)
    plt.yticks(fontsize=6)
    #ax.yaxis.set_label_coords(0, 0)
    plt.tight_layout()
    plt.grid(True)
    ax.xaxis.set_minor_locator(AutoMinorLocator())
    ax.yaxis.set_minor_locator(AutoMinorLocator())
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='major', direction='in', color='k')
    plt.tick_params(bottom=True, top=True, left=True, right=True, which='minor', direction='in', color='k')
    #plt.show()
    
    figure_canvas_agg = FigureCanvasTkAgg(figure, canvas)
    #figure_canvas_agg.get_tk_widget().pack_forget()
    figure_canvas_agg.draw()
    figure_canvas_agg.get_tk_widget().pack(side="right", fill="both", expand=1)

    return figure_canvas_agg


def clearPlotPage(self):
    self.canvas.get_tk_widget().pack_forget()
    self.canvas = None
    print("Plot Page has been cleared")

if __name__=="__main__":
    event, values = window.read()
    kthl = Keithley2400(float(values[0]),False)
    
    while True:
        event, values = window.read()
        if event==sg.WINDOW_CLOSED:
            break
        #if event=='Initiate':
        #    print('GPIB loaded:', values[0])
        
        if event=='Laser Sweep':
            try:
                wavelength,power=laser_sweep(float(values[3]), float(values[4]), float(values[5]))
                draw_power_vs_wavelength_figure(window['power_graph'].TKCanvas, wavelength, power)
                print('Wavelength Sweep at single iv source done')
                
                diction={}
                diction ['Wavelength (nm)']=wavelength 
                diction ['Power(dBm)']= power
                
                df=pd.DataFrame.from_dict(diction)
            except:
                print('Laser sweep was not successful')
        
        if event=='Save Data':
            try:
                df = pd.DataFrame(data=df)
                df.to_csv('laser_sweep.csv', index=False)                
                print('Laser sweep data saved successfully')
            except:
                print('No laser sweep data found')         
        
        if event=='Voltage Sweep':
            kthl.set_source_voltage()
            try:
                V=np.arange(float(values[6]), float(values[7]), float(values[8]))
                len(V)
                I=np.zeros(len(V))
                m=0
                
                diction={}
                for m in range (len(V)):
                    kthl.voltage=V[m]
                    kthl.output_on()
                    I[m]=kthl.current  #time.sleep(0.5)  #0.5 s delay
                    #laser sweep
                    wavelength,power=laser_sweep(float(values[3]), float(values[4]), float(values[5]))
                    diction ['Wavelength (nm)']=wavelength 
                    diction ['Power(dBm) @ ' + str (V[m]) +'V']= power                    
                    m=m+1
                kthl.output_off()
                
                df=pd.DataFrame.from_dict(diction) #dictionary to dataframe conversion
                data=df.to_numpy()                 #dataframe to numpy conversion
                
                #V,I=kthl.voltage_sweep(float(values[1]), float(values[2]), float(values[3]))   #kthl.voltage_sweep(0,-9,-0.1)                  
                draw_figure(window['iv_graph'].TKCanvas, V, I)
                draw_power_vs_wavelength_figure(window['power_graph'].TKCanvas, data[: , 0], data[:, 1])

                print('V=', V, ' I=', I, ' Voltage sweep done')
            except:
                print('Voltage sweep not successfull')

        if event=='Current Sweep':
            kthl.set_source_current()
            #iv_graph.erase()
            try:
                I=np.arange(float(values[9]), float(values[10]), float(values[11]))
                len(I)
                V=np.zeros(len(I))
                m=0
                
                diction={}
                for m in range (len(I)):
                    kthl.current=I[m]
                    kthl.output_on()
                    V[m]=kthl.voltage  #time.sleep(0.5)  #0.5 s delay
                    #laser sweep
                    wavelength,power=laser_sweep(float(values[3]), float(values[4]), float(values[5]))
                    diction ['Wavelength (nm)']=wavelength 
                    diction ['Power(dBm) @ ' + str (I[m]) +'A']= power                    
                    m=m+1
                kthl.output_off()                
                
                df=pd.DataFrame.from_dict(diction) #dictionary to dataframe conversion
                data=df.to_numpy()                 #dataframe to numpy conversion
                
                draw_figure(window['iv_graph'].TKCanvas, V, I)
                draw_power_vs_wavelength_figure(window['power_graph'].TKCanvas, data[: , 0], data[:, 1])

                print('V=', V, ' I=', I, ' Current sweep done')
            except:
                print('Current sweep not successfull')

        if event=='Save Sweep Data':
            try:
                df = pd.DataFrame(data=df)
                df.to_csv('keithley_sweep.csv', index=False)                
                print('Keithly sweep data saved successfully')
            except:
                print('No sweep data found') 
    # Finish up by removing from the screen
    window.close()                                 