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

def read_all_samples(GLITC, channel,wait_time=0.01):
	sample_values = np.zeros(32)
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		sample_values[sample_i]=trans[GLITC.train_read(channel, sample_i, 1)]
	return sample_values
	
def read_all_samples_n(GLITC, channel,num_trials):
	sample_values = [0]*32
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		for n in range(num_trials):
			sample_values[sample_i]+=float(trans[GLITC.train_read(channel, sample_i, 1)])
	#print sample_values
	return sample_values

def read_sample_n(GLITC, channel,sample_number,num_trials):
	sample_value = 0.0
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for n in range(num_trials):
		sample_value+=float(trans[GLITC.train_read(channel, sample_number, 1)])
	sample_value /=float(num_trials)
	return sample_value
	
def reset_all_thresholds(GLITC,RITC,reset_value=4095,wait_time=0.01):
	# Reset all thresholds to the highest value
	for i in range(21):
		sleep(wait_time)
		GLITC.rdac(RITC,i,4095)
		
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
					  	
def make_scatter_plot(pp,x,y,GLITC_n,channel,threshold_label,transition_value,pedestal,offset,flag):
	plt.figure(figsize=(16,12))	
	plt.scatter(x,y)
	if(flag==1):
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Transition "+str(transition_value))
		plt.xlabel("Threshold Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		plt.text(transition_value*1.05,1.0, ('Input DAC: %1.1d' % pedestal), fontsize = 18)
		plt.text(transition_value*1.05,0.7, ('Offset: %1.1d' % offset), fontsize = 18)
		plt.axis([x[0],x[len(x)-1],-0.1,1.2])
		
	else:
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Transition "+str(transition_value))
		plt.xlabel("Input Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		#plt.axis([x[0],x[len(x)-1],-0.1,1.2])
		
	#plt.savefig(pp, format='pdf')	
	plt.show()
	plt.clf()
	plt.close()

def plot_threshold_offsets():

	wait_time = 0.01
	transition_values = [2048,1024,1536]
	pedestal_values = [872,583,698]
	offset_values = [55,41,17]
	num_trials = 100
	sample_number = 0
	
	for GLITC_n in range(1):
		GLITC = GLITC_setup(GLITC_n)
		
		for channel in range(1):
			if (channel ==3):
				continue

			if (channel <= 2):
				RITC = 0
			elif (channel >2):
				RITC = 1

			#pp = PdfPages('/home/user/data/GLITC_'+str(GLITC_n)+'/transition_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_transitions.pdf')
			pp = None
			for thres_i in range(1):
				threshold_label = 7-thres_i
				
				# Reset all threshold to maximum
				reset_all_thresholds(GLITC,RITC)
				
				# Get the DAC numbers
				if (channel<= 2):
					RITC_COMP = ((channel*7)+thres_i)
				elif (channel >2):
					RITC_COMP = ((channel-4)*7)+thres_i
				
				### Take data from board ###########################
				for i in range(3):
					transition_value = transition_values[i]
					input_dac_transition_value = pedestal_values[i]
					offset = offset_values[i]
					print "Starting transition value %1.1d on RITC %1.1d threshold %1.1d" % (transition_value, RITC, threshold_label)
					# Set  threshold one count below transition point
					GLITC.rdac(RITC,RITC_COMP,transition_value-1)
					sleep(wait_time)
					
					GLITC.dac(channel,input_dac_transition_value)
					sleep(wait_time)

					graph_2_x = []
					graph_2_y = []

					sample_value_array = np.zeros(32)
					sample_value = 0.0

					for thres_i in range(transition_value-50,transition_value+150):
						#print "Setting threshold to %1.1d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
						# Step threshold dac value
						if(thres_i>=transition_value):
							threshold_value = thres_i+offset
						else:
							threshold_value = thres_i
						GLITC.rdac(RITC,RITC_COMP,threshold_value)
						sleep(wait_time)
						
						# Read in samples and check if it passes the sample transition point
						sample_value = read_sample_n(GLITC,channel,sample_number, num_trials)/float(threshold_label)

						graph_2_x.append(thres_i)
						graph_2_y.append(sample_value)

				####################################################
				
					make_scatter_plot(pp,graph_2_x,graph_2_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,offset,1)
			#pp.close()
				
if __name__ == "__main__":
	
	plot_threshold_offsets()
					


