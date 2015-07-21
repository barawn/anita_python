import ocpci
import struct
import sys
import tisc
from time import sleep, time
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
import csv
import datetime
from scipy.stats import norm
import matplotlib.mlab as mlab
import tisc_toolbox as ttb


def read_all_samples(glitc, channel,wait_time=0.01):
	sample_values = [0]*32
	


	for sample_i in range(0,32):
		#sleep(wait_time)
		sample_values[sample_i]=glitc.train_read(channel, sample_i, 1)
		#sleep(wait_time)
	return sample_values
	
def read_all_samples_n(glitc, channel,num_trials):
	sample_values = [0]*32
	

	for sample_i in range(0,32):
		for n in range(num_trials):
			sample_values[sample_i]+=glitc.train_read(channel, sample_i, 1)

	#sample_values = sample_values/num_trials
	return sample_values
	
def reset_all_thresholds(glitc,RITC,reset_value=4095,wait_time=0.01):
	# Reset all thresholds to the highest value
	for i in range(21):
		sleep(wait_time)
		GLITC.rdac(RITC,i,4095)
		#sleep(wait_time)
		
		
def stitch_threshold_dac(GLITC_n,channel,threshold_label,dac):
	dac_temp = dac
	
	offset_2048 = 54
	offset_1024 = 47
	offset_512 = 18
	offset_256 = 0
	offset_128 = 0
	
	if(dac>2047):
		dac+=offset_2048+offset_1024+2*offset_512+4*offset_256+8*offset_128
		#threshold_voltage.append((float(thres_i-dac_offset)/4095.)*1200.)
		dac_temp-=2048
	if(dac_temp>1023):
		dac+=offset_1024+offset_512+2*offset_256+4*offset_128
		dac_temp-=1024
	if(dac_temp>511):
		dac+=offset_512+offset_256+2*offset_128
		dac_temp-=512	
	if(dac_temp>255):
		dac+=offset_256+offset_128
		dac_temp-=256
	if(dac_temp>127):
		dac+=offset_128
		dac_temp-=128
	return dac









wait_time = 0.01

sample_values = []

for i in range(32):
	sample_values.append([])




starttime = time()
for GLITC_n in range(1):
	
	# Setup the GLITC
	ttb.setup(GLITC_n)
	
	print "Starting threshold/pedistal scan on GLITC "+str(GLITC_n)

	#loop over each channel, note our channel here goes left to right on the board.
	for channel_i in range(1):#,7):
		if (channel_i==3):
			continue
		if (channel_i <= 2):
			RITC = 0
		elif (channel_i >2):
			RITC = 1
			
		#datafile = open('/home/user/data/GLITC_'+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/Fine/channel_'+str(channel_i)+'_threshold_data_ultrafine.dat','w')
		#datafile.write('GLITC,Channel,Threshold_DAC,Threshold_dac_value,Pedestal_dac_value,sample_values_0_to_31\n')
		#with open('/home/user/data/GLITC_'+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/channel_'+str(channel_i)+'_threshold_data_stiched_dac.dat','wb') as f:
			#writer = csv.writer(f)
			#writer.writerow(['trial_number','glitc','channel','threshold_dac','threshold_dac_value','input_dac_value','sample_0_21'])
			#pp = PdfPages('/home/user/data/GLITC_'+str(GLITC_n)+'/test_GLITC_'+str(GLITC_n)+'_Ch_'+str(channel_i)+'_hist.pdf')

		if(True):
			pp=None

			for ped_i in range(500,1100+1,20): 
				print "Pedestal voltage on channel "+str(channel_i)+" set to "+str(ped_i*2500/4095)+'mV'
				#print "RITC "+str(RITC)+", DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200/4095)+'mV'
				
				GLITC.dac(channel_i, ped_i)
				sleep(5)

				#Loop over threshold levels (0-6)
				for thres_level in range(1):
					threshold_label = 7-thres_level
					
					# Get the DAC numbers
					if (channel_i<= 2):
						RITC_COMP = ((channel_i*7)+thres_level)
					elif (channel_i >2):
						RITC_COMP = ((channel_i-4)*7)+thres_level

					# Reset all thresholds to the highest value
					GLITC.reset_all_thresholds(RITC)
						
					sevens_counter = 0
					#threshold_array = []
					#transition_point = [0]*32
					#transition_flag = [0]*32
					
					min_threshold_range = 0
					max_threshold_range = 4095

					
					#print (("Starting threshold %1.1d") % (RITC_COMP))
					#loop over threshold values
					sample_values,threshold_array,transition_point = ttb.threshold_scan(GLITC,GLITC_n,channel,RITC,RITC_COMP,threshold_label,sample_number,pp)
					"""
					for thres_i in range(min_threshold_range,max_threshold_range+1,30):
						#print ("RITC "+str(RITC)+", Threshold DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200./4095.)+'mV')	
						#print thres_i
						threshold_array.append(thres_i)
						#thres_i = stitch_threshold_dac(GLITC_n,channel_i,threshold_label,thres_i)
						#print thres_i
						if(thres_i>max_threshold_range):
							break
						GLITC.rdac(RITC,RITC_COMP,thres_i)
						sleep(wait_time)
						
						sample_values = []
						sample_values_temp = [0]*32
						
						sample_values_temp_2 =0
						
						

						for i in range(38):
							sample_values.append([])
						
						num_trials = 10
						
						#sample_values_temp = read_all_samples_n(GLITC, channel_i, num_trials)
						
						
						sample_values[0].append(num_trials*1023)
						sample_values[1].append(GLITC_n)
						sample_values[2].append(channel_i)
						sample_values[3].append(RITC_COMP)
						sample_values[4].append(thres_i)
						sample_values[5].append(ped_i)
						for sample_number in range(32):
							sample_values_temp_2 =0
							
							for i in range(num_trials):
								sample_values_temp_2 += GLITC.scaler_read(channel_i,sample_number)/float(threshold_label*1023.0)
							#print sample_values_temp_2/float(num_trials)
							sample_values[sample_number+6].append(sample_values_temp_2/float(num_trials))
							if(sample_values_temp_2/float(num_trials)<1.0 and transition_flag[sample_number]!=1):
								transition_point[sample_number] = thres_i
								transition_flag[sample_number] = 1
						print sample_values_temp_2/float(num_trials)
						print transition_point[31]
						sample_values = np.transpose(sample_values)
						
						
						
						#writer.writerows(sample_values)
						
						#print sample_values	 
					"""	

								
					bin_width =  2*(threshold_array[1]-threshold_array[0])
					num_bins = int(4095.0/bin_width)
					max_bin = bin_width*num_bins
					
					plt.figure(figsize=(16,12))	
					
					(mu, sigma) = norm.fit(transition_point)
					bc_sigma = (1.0/np.sqrt(12))*float(bin_width)
					full_sigma = np.sqrt(sigma**2+bc_sigma**2)

					n,bins,patches = plt.hist(transition_point,num_bins,range=[0.-bin_width/2.,max_bin-bin_width/2.])
					test = mlab.normpdf(bins,mu,full_sigma)
					norm_factor = len(transition_point)*bin_width
					plt.plot(bins, norm_factor*test, 'r--', linewidth=2)
					
					plt.axvline(int(mu),color='b', linestyle='dashed',linewidth=2)
					plt.text(0,30, ((r'$\mu = %1.1d (%dmV),\  \sigma = %1.1d (%dmV)$') % (mu,mu*1200./4095.,full_sigma,full_sigma*1200./4095.)), fontsize = 20)
					plt.text(0,28, (r'$Bin\ width = %1.1d (%dmV)$' % (bin_width,bin_width*1200/4095)), fontsize = 20)
					plt.xlabel("Transition Threshold Value (mV)")
					plt.ylabel("Counts")
					plt.axis([-bin_width,4095,0,33])
					ax = plt.gca()
					ax.set_autoscale_on(False)
					plt.title(("GLITC %1.1d, Ch %1.1d, Threshold %1.1d, Input: %1.1dmV Transition Points") % (GLITC_n, channel_i, threshold_label, ped_i*2500./4095.))
					#plt.legend(bbox_to_anchor=(0.90,1),loc=2,borderaxespad=0.)
					#plt.savefig(("GLITC_%1.1d/plots/Ch_%1.1d/ch_%1.1d_ped_%1.1d.png") % (int(GLITC),int(channel), int(channel), (int(pedestal_value[row_i-2]))*2500.0/4095.0))
					if(pp!=None):
						plt.savefig(pp, format='pdf')
					plt.show()
					plt.clf()
					plt.close()
		
						
					#set this threshold level threashold back to zero (highest threshold) before moving to the next.
					#GLITC.rdac(RITC,RITC_COMP,0)
				sleep(wait_time)
			if(pp!=None)
				pp.close()
			#datafile.close()
stoptime = time()
print "Stopped at: "+str(stoptime)
print "Took: "+str(stoptime-starttime)
					


