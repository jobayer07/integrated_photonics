import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
from scipy.signal import find_peaks
from scipy import signal
import os
import glob
import csv
from scipy import interpolate

#--------------------User Input--------------------------
path='27SOF0'
device_id_list=[1, 3, 5, 7]

level='wafer'           #'wafer', 'die'
die_id='5_7'            #Needed only if level='die'
test_id='1550JJRK40'

ring_radius_list=[7e-6, 7e-6, 7e-6, 7e-6] #in m
coupling_length_list=[0, 0, 0, 0]

peak_detection_threshold=3
peak_detection_spacing=10

plot_frontSize=16 

#----------------------------------------------Functions------------------------

def raw_data_baseline_correction(df, deg):
    df = pd.read_csv(str(raw_data_file), skiprows=5311, usecols=[0, device_id*2+1], header=None)
    df.columns = range(df.columns.size)   #renames column as 0 and 1
    df=df.dropna() 
    
    poly = np.polyfit(df[0], df[1], deg=deg)
    loss_trend = np.polyval(poly, df[0])                      #finding the trend using 3rd order polynomial fitting

    trend_adjustment=min(loss_trend)-min(df[1])
    loss_trend_shifted =  loss_trend-trend_adjustment   #adjusting the losser trend
    df[1]=df[1]-loss_trend_shifted
    return df

def pairwiseAvg(lst):
    size = len(lst)
    x=np.zeros(size-1)
    for i in range(len(lst)-1):
        x[i] = int((lst[i] + lst[i + 1])/2)
    return x

def find_index_of_nearest_value(array, value):
    idx = (np.abs(array - value)).argmin()
    return idx

def find_mid_index_er(d):
    peak_position, peak_value = find_peaks(d, height=peak_detection_threshold, distance=peak_detection_spacing)
    mid_index=pairwiseAvg(peak_position)  
    
    pairwisePeak=pairwiseAvg(peak_value.get('peak_heights'))
    mid_value=d[mid_index]
    
    er=pairwisePeak-mid_value                                   #extinction ratio
    return mid_index, er

def ng_calculation(d, mid_index, fsr, r, CL):
    fsr=fsr
    lam=d[mid_index] -fsr/2 # By -fsr/2, we calculate at the resonance peaks
    L=2*np.pi*r + 2*CL
    ng=(lam**2)/(L*fsr)
    return ng

def wavelength_interpolation(x,y, xnew): 
    tck = interpolate.splrep(x, y, s=40)     #s=0 -> No smoothing/regression required
    ynew = interpolate.splev(xnew, tck, der=0)
    return ynew

#----------------------------------------------Main Program----------------------------
os.chdir(path)
summary = {'Device ID': [0], 'Extinction ratio mean': [0], 'Extinction ratio std': [0], 'FSR mean': [0], 'FSR std': [0], 'Group Index mean': [0], 'Group Index std': [0]}

for k in range (len(device_id_list)):
    device_id=device_id_list[k]
    ring_radius=ring_radius_list[k]
    coupling_length=coupling_length_list[k]
    
    if (level=='die'):
        try:
            files_list=glob.glob('*L'+str(device_id)+'_'+'*'+str(test_id)+'*'+str(die_id)+'.csv')
        except:
            files_list=glob.glob('*L'+str(device_id)+'_'+'*'+str(die_id)+'.csv')
        
    elif (level=='wafer'):
        try:
            files_list=glob.glob('*L'+str(device_id)+'_'+'*'+str(test_id)+'*'+'.csv')
        except:
            files_list=glob.glob('*L'+str(device_id)+'_'+'*'+'*'+'.csv')
    #print(files_list)


    #For both wafer and die level
    if not files_list:
        print('Device', device_id, ' is absent')
    else:

        fig, ([ax0, ax1], [ax2, ax3]) = plt.subplots(nrows=2, ncols=2, sharex=False, figsize=(18, 12))
        
        er_list=[]
        fsr_list=[]
        ng_list=[]
        for i in range(len(files_list)):
            raw_data_file=files_list[i]
            df=raw_data_baseline_correction(raw_data_file, deg=3.8)
            
            mid_pos, er=find_mid_index_er(df[1])
            peak_position, peak_value = find_peaks(df[1], height=peak_detection_threshold, distance=peak_detection_spacing)
            delta_wl=(df[0][len(df[0])-1]-df[0][0])/(len(df[0])-1)
            fsr=np.diff(peak_position)*delta_wl
            ng=ng_calculation(df[0], mid_pos, fsr, ring_radius, coupling_length)
            
            ax0.plot(df[0]*1e9, df[1])
            ax0.set_xlabel('Wavelength (nm)', fontsize=plot_frontSize)
            ax0.set_ylabel('Normalized loss (dB)', fontsize=plot_frontSize)
            
            ax1.plot(df[0][mid_pos]*1e9, er)
            ax1.set_xlabel('Wavelength (nm)', fontsize=plot_frontSize)
            ax1.set_ylabel('Extinction ratio (dB)', fontsize=plot_frontSize)
            
            ax2.plot(df[0][mid_pos]*1e9, fsr*1e9)
            ax2.set_xlabel('Wavelength (nm)', fontsize=plot_frontSize)
            ax2.set_ylabel('Free spectral range (nm)', fontsize=plot_frontSize)
            
            ax3.plot(df[0][mid_pos]*1e9, ng)
            ax3.set_xlabel('Wavelength (nm)', fontsize=plot_frontSize)
            ax3.set_ylabel('Group index', fontsize=plot_frontSize)
            
            
            if (level=='die'):
                fig.suptitle(str(level)+' level ('+str(die_id)+') characteristics of device L'+ str(device_id), fontsize=28)
            elif (level=='wafer'):
                    fig.suptitle(str(level)+' level characteristics of device L'+ str(device_id), fontsize=28)
                    er_list.append(wavelength_interpolation(df[0][mid_pos]*1e9,er, 1550))
                    fsr_list.append(wavelength_interpolation(df[0][mid_pos]*1e9,fsr*1e9, 1550))
                    ng_list.append(wavelength_interpolation(df[0][mid_pos]*1e9,ng, 1550))
                    
        fig.savefig(str(level)+'_level_L'+ str(device_id) + '.png', bbox_inches='tight', dpi=100)
                    
        er_arr=np.array(er_list)
        fsr_arr=np.array(fsr_list)
        ng_arr=np.array(ng_list)

        mean_er=np.mean(er_arr)
        std_er=np.std(er_arr)
        mean_fsr=np.mean(fsr_arr)
        std_fsr=np.std(fsr_arr)        
        mean_ng=np.mean(ng_arr)
        std_ng=np.std(ng_arr)
        
        summary['Device ID'].append(device_id)
        summary['Extinction ratio mean'].append(mean_er)
        summary['Extinction ratio std'].append(std_er)
        summary['FSR mean'].append(mean_fsr)
        summary['FSR std'].append(std_fsr)
        summary['Group Index mean'].append(mean_ng)
        summary['Group Index std'].append(std_ng)

summary=pd.DataFrame.from_dict(summary)
summary = summary.drop(summary.index[[0]])
summary.to_csv(str(level)+'_level_summary.csv', index=False)
        