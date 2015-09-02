import tisc_toolbox as ttb
import tisc
from time import sleep
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.stats import norm
from matplotlib.backends.backend_pdf import PdfPages
import csv


max_dac = 1200
min_dac = 400
step_dac = 100
num_trials = 10
wait_time = 0.01

file_iterator = "5_set_midpoint_extended_high_end"


for GLITC_i in range(1):
	
	GLITC = ttb.setup(GLITC_i)
	
	for channel_i in range(7):
		
		if (channel_i==3): continue
		
		print "\nStarting GLITC %d, Ch %d\n"%(GLITC_i,channel_i)
		
		ttb.set_thresholds(GLITC,GLITC_i,channel_i)
		
		#threshold_label = 7 # Not used
			
		#RITC,RITC_COMP = ttb.get_channel_info(channel_i,threshold_label)
			
		sample_array,input_array = ttb.input_dac_scan(GLITC,GLITC_i,channel_i,min_dac,max_dac,step_dac,num_trials,wait_time)

		overlay_fig = plt.figure(1,figsize=(16,12))
		individual_fig = plt.figure(2,figsize=(16,12))
		pp = PdfPages('/home/user/data/GLITC_%d/threshold_study/G%d_Ch%d_input_scan_samples_%s.pdf'%(GLITC_i,GLITC_i,channel_i,file_iterator))
		colors = iter(cm.brg(np.linspace(0,1,32)))
		
		
		for i in range(32):
			color = next(colors)
			plt.figure(1)
			plt.plot(input_array,sample_array[i],color=color,label=("Sample: %d" % i))
			plt.title("GLITC "+str(GLITC_i)+", Ch "+str(channel_i))
			plt.xlabel("Input Voltage (DAC Counts)")
			plt.ylabel("Normalized Output Value")
			plt.legend()
			#plt.savefig(pp,format='pdf')
			#plt.show()
			plt.clf()
			
			plt.figure(2)
			plt.plot(input_array,sample_array[i],color=color,label=("Sample: %d" % i))
			plt.title("GLITC "+str(GLITC_i)+", Ch "+str(channel_i))
			plt.xlabel("Input Voltage (DAC Counts)")
			plt.ylabel("Normalized Output Value")

		
		plt.figure(2)
		#plt.savefig('/home/user/data/GLITC_'+str(GLITC_i)+'/threshold_study/G'+str(GLITC_i)+'_Ch'+str(channel_i)+'_input_scan_'+str(file_iterator)+'.png')
		plt.show()
		pp.close()
		plt.clf()
		
		

		
