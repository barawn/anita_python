
import csv
import matplotlib.pyplot as plt
import numpy as np
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
import ocpci
import struct
import sys
import tisc
from time import sleep, time
import datetime
from scipy.stats import norm

def read_all_samples(GLITC, channel,wait_time=0.01):
	sample_values = np.zeros(32)
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		sample_values[sample_i]=GLITC.train_read(channel, sample_i, 1)
	return sample_values
	
def read_all_samples_n(GLITC, channel,num_trials):
	sample_values = [0]*32
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		for n in range(num_trials):
			sample_values[sample_i]+=float(GLITC.train_read(channel, sample_i, 1))
	#print sample_values
	return sample_values

def read_sample_n(GLITC, channel,sample_number,num_trials):
	sample_value = 0.0
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for n in range(num_trials):
		sample_value+=float(GLITC.train_read(channel, sample_number, 1))
	sample_value /=float(num_trials)
	return sample_value

def read_scaler_value(GLITC,channel,sample_number):
	sample_value = GLITC.scalar_read(channel,sample_number)/1023.0
	return sample_value
	
#def reset_all_thresholds(GLITC,RITC,reset_value=4095,wait_time=0.01):
	# Reset all thresholds to the highest value
	#for i in range(21):
		#sleep(wait_time)
		#GLITC.rdac(RITC,i,4095)
			
def GLITC_setup(GLITC_n, wait_time=0.01):
	dev = tisc.TISC()
	# Initialize the data path and set the Vdd & Vss points
	if (GLITC_n == 0):
		print "starting glitc 0"		
		GLITC = dev.GA
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1735)
		sleep(wait_time)
		GLITC.rdac(0,32,3500)
		sleep(wait_time)
		GLITC.rdac(1,31,1645)
		sleep(wait_time)
		GLITC.rdac(1,32,3500)
		sleep(wait_time)
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
	elif (GLITC_n == 1):	
		#print "starting glitc 1"		
		GLITC = dev.GB
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1645)
		sleep(wait_time)
		GLITC.rdac(0,32,3500)
		sleep(wait_time)
		GLITC.rdac(1,31,1765)
		sleep(wait_time)
		GLITC.rdac(1,32,3500)
		sleep(wait_time)
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
	elif (GLITC_n == 2):	
		#print "starting glitc 2"		
		GLITC = dev.GC
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1735)
		sleep(wait_time)
		GLITC.rdac(0,32,3500)
		sleep(wait_time)
		GLITC.rdac(1,31,2055)
		sleep(wait_time)
		GLITC.rdac(1,32,3500)
		sleep(wait_time)
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
	elif (GLITC_n == 3):
		#print "starting glitc 3"	
		GLITC = dev.GD
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1765)
		sleep(wait_time)
		GLITC.rdac(0,32,3500)
		sleep(wait_time)
		GLITC.rdac(1,31,1770)
		sleep(wait_time)
		GLITC.rdac(1,32,3500)
		sleep(wait_time)
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
	
	# Turn off training
	GLITC.training_ctrl(0)
	sleep(wait_time)
	return GLITC


def make_data_histogram():
	
	#GLITC,CHANNEL,RITC_COMP,threshold_lable,dac_setting,Ped_setting,sample
	#0,0,0,7,1536,699,0
	#0,0,0,7,2048,872.0
	#1,0,1,6,2048,857,4
	#1,2,18,3,1536,683,4
	GLITC_n = 1
	channel = 2
	RITC_COMP = 18
	threshold_label = 3
	input_threshold_setting = 1535
	input_ped = 683
	sample_number = 4
	
	
	GLITC = GLITC_setup(GLITC_n)
		
	
	if (channel ==3):
		print 'invalid channel!'
	if (channel <= 2):
		RITC = 0
		#RITC_COMP = ((channel*7)+threshold)
	elif (channel >2):
		RITC = 1
		#RITC_COMP = ((channel-4)*7)+threshold
	
	# Reset all threshold to maximum
	GLITC.reset_all_thresholds(RITC)
	wait_time = 0.01
	
	num_trials = 64
	num_datapoints = 500
	histogram_data = [0]*num_datapoints
	
	#Set Ped and dac_count for nearish 50% point, 
	GLITC.dac(channel,input_ped)   
	sleep(5)
	GLITC.rdac(RITC,RITC_COMP, input_threshold_setting)
	sleep(wait_time)
	
	
	#Take data, much data.
	for j in range(num_datapoints):
		sample = 0
		for i in range(num_trials):
			sample += GLITC.scaler_read(channel,sample_number)/float(threshold_label*1023.0)
			sleep(wait_time)
		sample/=float(num_trials)
		histogram_data[j] = sample
	
	
	#print histogram_data
	#Now we have our data, lets histogram it up.
	
	bin_range = [0,1]
	bin_width = 0.01
	bin_num = int((bin_range[1]-bin_range[0])/bin_width)
	bc_sigma = (1.0/np.sqrt(12))*float(bin_width)
	plt.figure(figsize=(16,12))	

	#plt.hist(histogram_data,bin_num,range=bin_range,label=('%1.2f samples per point' % (num_trials*1024)))

	(mu, sigma) = norm.fit(histogram_data)
	full_sigma = np.sqrt(sigma**2+bc_sigma**2)
	plt.hist(histogram_data,bin_num,range=bin_range,label=('%1.2f samples per point, $\mu=%1.4f, \sigma=%1.4f$' % ((num_trials*1024),mu,full_sigma)))
	print 'mu=%1.4f, \sigma=%1.4f' % (mu,full_sigma)

	plt.xlabel("Normalized Output Value")
	plt.ylabel("Counts")
	plt.title(('Data Varience for statistics of n = %1.2f' % (num_trials*1024) ))
	plt.text(60,25, (r'$Bin\ width = %1.1d $' % bin_width), fontsize = 20)
	plt.legend()
	plt.show()
	#plt.savefig(pp, format='pdf')
	plt.clf()
	plt.close()
	
	
if __name__ == "__main__":
	
	make_data_histogram()
	
