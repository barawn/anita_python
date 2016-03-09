
import matplotlib.pyplot as plt
import tisc
from time import sleep, strftime, time
import numpy as np
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import leastsq
from scipy.fftpack import fft
import csv
import matplotlib.gridspec as gridspec
from scipy.stats import norm
import math
import os


#note, as the dictionaries are stored in the TISC# subfolders of data,
#if you want to switch to a different board you will need to change the 
#TISC variable, save, and reload tisc_toolbox in python
TISC = 10005
import imp
#If these dictionaries dont exist yet, these lines need to be commented out untill they are created.
if os.path.isfile('/home/user/data/TISC%d/TISC_VSS_VDD_setting_dictionary.py'%TISC):
	tvd = imp.load_source('tvd', '/home/user/data/TISC%d/TISC_VSS_VDD_setting_dictionary.py'%TISC)
if os.path.isfile('/home/user/data/TISC%d/TISC_threshold_offset_dictionary.py'%TISC):
	tod = imp.load_source('tod', '/home/user/data/TISC%d/TISC_threshold_offset_dictionary.py'%TISC)
if os.path.isfile('/home/user/data/TISC%d/TISC_threshold_setting_dictionary.py'%TISC):
	tsd = imp.load_source('tsd', '/home/user/data/TISC%d/TISC_threshold_setting_dictionary.py'%TISC)
if os.path.isfile('/home/user/data/TISC%d/TISC_INL_correction_dictionary.py'%TISC):
	INLd = imp.load_source('INLd', '/home/user/data/TISC%d/TISC_INL_correction_dictionary.py'%TISC)


#
import ocpci
import struct
import sys
from matplotlib.backends.backend_pdf import PdfPages
import datetime
import matplotlib.mlab as mlab



def setup(GLITC_n,wait_time=0.01):
	    
	# Initialize the data path and set the Vdd & Vss points
	if (GLITC_n == 0):
		print "starting glitc 0"		
		GLITC = tisc.TISC().GA
	elif (GLITC_n == 1):	
		print "starting glitc 1"		
		GLITC = tisc.TISC().GB
	elif (GLITC_n == 2):
		print "starting glitc 2"		
		GLITC = tisc.TISC().GC
	elif (GLITC_n == 3):
		print "starting glitc 3"	
		GLITC = tisc.TISC().GD
	else:
		print "Invalid GLITC number!"
		return 1
	GLITC.datapath_initialize()
	sleep(wait_time)
	GLITC.write(0x40,0x1)
	sleep(wait_time)
	VSS,VDD = tvd.get_VSS_VDD_setting(TISC,GLITC_n,0)
	GLITC.rdac(0,31,VSS)
	sleep(wait_time)
	GLITC.rdac(0,32,VDD)
	sleep(wait_time)
	VSS,VDD = tvd.get_VSS_VDD_setting(TISC,GLITC_n,1)
	GLITC.rdac(1,31,VSS)
	sleep(wait_time)
	GLITC.rdac(1,32,VDD)
	sleep(wait_time)
	GLITC.training_ctrl(1)
	sleep(wait_time)
	GLITC.eye_autotune_all()
	sleep(wait_time)
	GLITC.training_ctrl(0)
	sleep(wait_time)
	return GLITC


def get_channel_info(channel,threshold_label):
	
	if(channel<3):
		RITC=0
	elif(channel>3):
		RITC=1
	
	# Get the DAC numbers
	if (channel<= 2):
		RITC_COMP = ((channel*7)+7-threshold_label)
	elif (channel >2):
		RITC_COMP = ((channel-4)*7)+7-threshold_label
		
	return RITC, RITC_COMP

	
def set_thresholds(GLITC,GLITC_n,channel,wait=0.01):
	#reload(tsd)
	
	
	sample_array = []

	
	for thres_i in range(7):
		threshold_label = 7-thres_i
		RITC, RITC_COMP = get_channel_info(channel,threshold_label)
		threshold_value = tsd.get_threshold(TISC,GLITC_n,channel,RITC_COMP)
		#print "Setting threshold %d to %d"%(threshold_label,threshold_value)
		GLITC.rdac(RITC,RITC_COMP,threshold_value)
		sleep(wait)
		
		
	return None	


def set_higher_thresholds_to_max(GLITC,GLITC_n,channel,threshold_label):
	threshold_level_i = 7-threshold_label
	
	RITC,RITC_COMP = get_channel_info(channel,threshold_label)
	
	for threshold_level_ii in range(0,threshold_level_i):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)

	
def find_bit_transition(GLITC,GLITC_n,channel,RITC,RITC_COMP,transition_value,threshold_label,sample_number,pp,num_trials=10,wait_time=0.01):
	
	#RITC,RITC_COMP = get_channel_info(channel,threshold_label)
	# Reset values
	minimum_input_value = int(transition_value*1200./2500.)-200
	maximum_input_value = int(transition_value*1200./2500.)+200
	initial_input_value = int(transition_value*1200./2500.) #Convert from Threshold voltage to pedestal voltage
	
	previous_input_value_low = minimum_input_value
	previous_input_value_high = maximum_input_value
	input_dac_value = initial_input_value
	
	sample_value_array = np.zeros(32)
	sample_counter = 0
	bad_sample_counter = 0
	sample_value = 0.0
	point_found = False
	no_midpoint_counter = 0

	graph_1_x = []
	graph_1_y = []
	
	
	print "Starting transition value %1.1d on RITC %1.1d threshold %1.1d" % (transition_value, RITC, threshold_label)
	# Set  threshold one count below transition point
	GLITC.rdac(RITC,RITC_COMP,transition_value-1)
	sleep(wait_time)


	# Adjust input voltages to find 50%+-10% point
	while (point_found != True):
		sample_value_array_temp = []
		# Set input voltage
		GLITC.dac(channel,input_dac_value)
		sleep(5)
		print "Setting input to %1.1d (%1.2fmV)" % (input_dac_value, input_dac_value*2500./4095.)
		#print sample_number
		# Read in and average values (may need to change to look at only one sample)
		#sample_value = read_sample_n(GLITC,channel, sample_number, num_trials)/float(threshold_label)
		sample_value = GLITC.scaler_read(channel,sample_number,num_trials)-threshold_label+1
		#print threshold_label-1
		#print sample_value
		
		
		if(sample_value>1.0):
			print "Bad sample found: %f" % sample_value
			bad_sample_counter+=1
			if(sample_number<31):
				sample_number+=1
			else:
				sample_number = 0
			
			
			if(bad_sample_counter<5):
				print "Bad sample #"+str(bad_sample_counter)+", moving to sample "+str(sample_number)
				continue

		graph_1_x.append(input_dac_value)
		graph_1_y.append(sample_value+threshold_label-1)
		
		# If point is between 40% and 60%, call it found
		if (sample_value >= 0.4 and sample_value <= 0.6):
			input_dac_transition_value = input_dac_value
			sample_transition_value = sample_value
			point_found = True
			print "Sample = %1.2f, Found transition point at %1.1d (%1.2fmV)" % (sample_transition_value,input_dac_transition_value, input_dac_transition_value*2500./4095.)
			
		# Input voltage is too low, increase the input dac if point is below 40% 
		elif(sample_value < 0.4 and sample_value > 0):
			previous_input_value_low = input_dac_value
			input_dac_value = int(input_dac_value+abs(previous_input_value_high-input_dac_value)/4.0)
			if(input_dac_value >2000):
				print "Input value out of range!"
				return None
			print "Sample = %1.2f, input is too low\r" % sample_value
		
		# Input voltage is too high, decrease the input dac if point is above 60% 
		elif(sample_value > 0.6 and sample_value < 1.0):
			previous_input_value_high = input_dac_value
			input_dac_value = int(input_dac_value-abs(input_dac_value-previous_input_value_low)/4.0)
			if(input_dac_value < 0):
				print "Input value out of range!"
				return None
			print "Sample = %1.2f, input is too high\r" % sample_value
			
		# Input voltage is too low, increase the input dac if point is below 40% 
		elif(sample_value < 0.4):
			previous_input_value_low = input_dac_value
			input_dac_value = int(input_dac_value+abs(previous_input_value_high-input_dac_value)/2.0)
			if(input_dac_value >2000):
				print "Input value out of range!"
				return None
			print "Sample = %1.2f, input is too low\r" % sample_value
			
			
		# Input voltage is too high, decrease the input dac if point is above 60% 
		elif(sample_value > 0.6):
			previous_input_value_high = input_dac_value
			input_dac_value = int(input_dac_value-abs(input_dac_value-previous_input_value_low)/2.0)
			if(input_dac_value < 0):
				print "Input value out of range!"
				return None
			print "Sample = %1.2f, input is too high\r" % sample_value
		
		# Narrowed down to a signal input value, but output was never between 0.4 and 0.6
		if(input_dac_value == previous_input_value_high or input_dac_value == previous_input_value_low and point_found != True):
			no_midpoint_counter+=1
			if(no_midpoint_counter>5):
				input_dac_transition_value = input_dac_value
				sample_transition_value = sample_value
				point_found = True
				print "Transition too sharp, using closest input DAC value"
				print "Sample = %1.2f, Found transition point at %1.1d (%1.2fmV)" % (sample_transition_value,input_dac_transition_value, input_dac_transition_value*2500./4095.)
			else:
				if(sample_number<31):
					sample_number+=1
				else:
					sample_number = 0
				print "Narrowed down to one input value but no midpoint found, switching to sample number %d" % sample_number
				previous_input_value_low = minimum_input_value
				previous_input_value_high = maximum_input_value
				input_dac_value = initial_input_value
				graph_1_x = []
				graph_1_y = []
			
			
		
	#make_scatter_plot(pp,graph_1_x,graph_1_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,0)
	
	return input_dac_transition_value,sample_transition_value,sample_number


def find_threshold_transition_point(sample_array,threshold_array,threshold_label):
	transition_point = [0]*32
	
	for i in range(len(sample_array[sample_i])):	
		if(sample_array[sample_i][i]<threshold_label-0.5):
			transition_point[sample_i] = threshold_array[i]
			break
	return transition_point


def find_bit_transition_all_samples(GLITC,GLITC_n,channel,RITC,RITC_COMP,transition_value,threshold_label,sample_number,pp,num_trials=10,wait_time=0.01):
	
	#RITC,RITC_COMP = get_channel_infor(channel,threshold_label)
	# Reset values
	input_width=200
	input_floor = 500
	input_ceiling = 1100
	minimum_input_value = int(transition_value*1200./2500.)-input_width
	maximum_input_value = int(transition_value*1200./2500.)+input_width
	initial_input_value = int(transition_value*1200./2500.) #Convert from Threshold voltage to pedestal voltage

	if(minimum_input_value<input_floor):
		print "Input at the floor"
		minimum_input_value = input_floor
		maximum_input_value = input_floor+input_width*2
		initial_input_value = input_floor+input_width
	elif(maximum_input_value>input_ceiling):
		print "Input at the ceiling"
		maximum_input_value=input_ceiling
		minimum_input_value=input_ceiling-input_width*2
		initial_input_value=input_ceiling-input_width
	
	previous_input_value_low = minimum_input_value
	previous_input_value_high = maximum_input_value
	input_dac_value = initial_input_value
	
	sample_value_array = np.zeros(32)
	sample_counter = 0
	bad_sample_counter = 0
	sample_value = 0.0
	point_found = False
	no_midpoint_counter = 0

	graph_1_x = []
	graph_1_y = []
	
	
	print "Starting transition value %1.1d on RITC %1.1d threshold %1.1d" % (transition_value, RITC, threshold_label)
	# Set  threshold one count below transition point
	GLITC.rdac(RITC,RITC_COMP,transition_value-1)
	sleep(wait_time)

	closest_sample_difference = 10000.0
	# Adjust input voltages to find 50%+-10% point
	while (point_found != True):
		sample_value_array = []
		
		# Set input voltage
		GLITC.dac(channel,input_dac_value)
		sleep(5)
		print "Setting input to %1.1d (%1.2fmV)" % (input_dac_value, input_dac_value*2500./4095.)

		# Read in values
		sample_value_array = GLITC.scaler_read_all(channel,num_trials)

		
		average_sample_value = np.mean(sample_value_array)-threshold_label+1	
		
		for sample_i in range(32):
			sample_value = sample_value_array[sample_i]-threshold_label+1
			
			if(abs(sample_value-0.5)<closest_sample_difference):
				closest_input_dac_value = input_dac_value
				closest_sample_difference = abs(sample_value-0.5)
				closest_sample_value = sample_value
				closest_sample_number = sample_i
				#print "Closest sample number: %d"% closest_sample_number
				#print "Closest sample value: %d"% closest_sample_value
				#print "Closest sample difference: %f"% closest_sample_difference
				#print "Closest input dac value: %d"%closest_input_dac_value
				
		# If point is between 40% and 60%, call it found
		if (closest_sample_value >= 0.4 and closest_sample_value <= 0.6):
			input_dac_transition_value = closest_input_dac_value
			sample_transition_value = closest_sample_value
			sample_number = closest_sample_number
			point_found = True
			print "Sample #%d = %1.2f, Found transition point at %1.1d (%1.2fmV)" % (sample_number,sample_transition_value,input_dac_transition_value, input_dac_transition_value*2500./4095.)
			break		

		# Input voltage is too low, increase the input dac if point is below 40% 
		elif(average_sample_value < 0.5 and average_sample_value > 0):
			previous_input_value_low = input_dac_value
			input_dac_value = int(input_dac_value+abs(previous_input_value_high-input_dac_value)/4.0)
			if(input_dac_value >2000):
				print "Input value out of range!"
				return None
			print "Average Sample = %1.2f, input is too low\r" % sample_value
		
		# Input voltage is too high, decrease the input dac if point is above 60% 
		elif(average_sample_value >= 0.5 and average_sample_value < 1.0):
			previous_input_value_high = input_dac_value
			input_dac_value = int(input_dac_value-abs(input_dac_value-previous_input_value_low)/4.0)
			if(input_dac_value < 0):
				print "Input value out of range!"
				return None
			print "Average Sample = %1.2f, input is too high\r" % sample_value
			
		# Input voltage is too low, increase the input dac if point is below 40% 
		elif(average_sample_value < 0.5):
			previous_input_value_low = input_dac_value
			input_dac_value = int(input_dac_value+abs(previous_input_value_high-input_dac_value)/2.0)
			if(input_dac_value >2000):
				print "Input value out of range!"
				return None
			print "Average Sample = %1.2f, input is too low\r" % sample_value
			
			
		# Input voltage is too high, decrease the input dac if point is above 60% 
		elif(average_sample_value > 0.5):
			previous_input_value_high = input_dac_value
			input_dac_value = int(input_dac_value-abs(input_dac_value-previous_input_value_low)/2.0)
			if(input_dac_value < 0):
				print "Input value out of range!"
				return None
			print "Average Sample = %1.2f, input is too high\r" % sample_value
			
		
		
		# Narrowed down to a signal input value, but output was never between 0.4 and 0.6
		if(input_dac_value == previous_input_value_high or input_dac_value == previous_input_value_low and point_found != True):
			if(closest_input_dac_value!=800):
				print "Setting input to %1.1d (%1.2fmV)" % (closest_input_dac_value, closest_input_dac_value*2500./4095.)
				GLITC.dac(channel,closest_input_dac_value)
				sleep(5)
		
			input_dac_transition_value = closest_input_dac_value
			sample_number = closest_sample_number
			sample_transition_value = closest_sample_value
			
			point_found = True
			print "Transition too sharp, using closest input DAC value and sample number"
			print "Sample # %d = %1.2f, Found transition point at %1.1d (%1.2fmV)" % (sample_number,sample_transition_value,input_dac_transition_value, input_dac_transition_value*2500./4095.)
			
		
	make_scatter_plot(pp,graph_1_x,graph_1_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,0)
	
	return input_dac_transition_value,sample_transition_value,sample_number

							  	
def make_scatter_plot(pp,x,y,GLITC_n,channel,threshold_label,transition_value,pedestal,offset,sample_number,flag):
	plt.figure(figsize=(16,12))	
	plt.scatter(x,y)
	if(flag==1):
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Transition "+str(transition_value)+', Sample Number '+str(sample_number))
		plt.xlabel("Threshold Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		plt.text(transition_value*1.02,threshold_label, ('Input DAC: %1.1d' % pedestal), fontsize = 18)
		#plt.axis([transition_value-150,transition_value+150,threshold_label-1.1,threshold_label+0.1])
		
	elif(flag==0):
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Transition "+str(transition_value)+', Sample Number '+str(sample_number))
		plt.xlabel("Input Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		#plt.axis([x[len(x)-1],x[0],threshold_label-1.1,threshold_label+0.1])
	else:
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Transition "+str(transition_value)+', Sample Number '+str(sample_number)+' - Corrected')
		plt.xlabel("Threshold Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		plt.text(transition_value*1.02,threshold_label, ('Input DAC: %1.1d' % pedestal), fontsize = 18)
		plt.text(transition_value*1.02,threshold_label-0.3, ('Offset: %1.1d' % offset), fontsize = 18)
		#plt.axis([transition_value-150,transition_value+150,threshold_label-1.1,threshold_label+0.1])
	if(pp!=None):
		plt.savefig(pp, format='pdf')	
	#plt.show()
	plt.clf()
	plt.close()
	
	
def find_rough_offset(sample_array,transition_value_index):
	offset=1
	sample_before_transition = sample_array[transition_value_index-1]
	#print transition_value_index
	#print "Sample before transition %f" % sample_before_transition
	#print sample_array[transition_value_index-10:transition_value_index+10]
	for i in range(transition_value_index,len(sample_array)):
		#print "Test_sample %f"%(sample_array[i])
		if(sample_array[i]<sample_before_transition):
			offset = i-transition_value_index
			break
	return offset
	
	
def find_slope_offset(GLITC,channel,threshold_label,sample_number,transition_point,rough_offset,num_trials=100):
		
	RITC,RITC_COMP = get_channel_info(channel,threshold_label)
	


	#rough_offset = offset
	offset = rough_offset
	min_offset = 1
	rms_error = [0]*3
	bad_slope_flag = 0
	print "Rough offset: %d" % rough_offset
	while(True):
		sample_at = 0
		sample_before = 0
		sample_after = [0]*3	
		delta_minus = 0
		delta_plus = [0]*3
		first_slope_flag=0
		bad_counter = 0
		#print "Starting delta_minus"
		
		while(first_slope_flag!=1):
			sleep(0.01)
			GLITC.rdac(RITC,RITC_COMP,transition_point-1)
			sleep(0.01)
			
			sample_at=GLITC.scaler_read(channel,sample_number)-threshold_label+1

			#print RITC
			#print RITC_COMP
			#New way to calculate delta_minus
			inside_flag = True #goes to False when outside range (0.5-0.78)
			slope_counter = 1 #this is the number of slopes that goes into calculating the avg slope
			delta_minus = 0
			while (inside_flag):
				#print "DAC setting %d" % (transition_point-1-slope_counter)
				sleep(0.01)
				GLITC.rdac(RITC,RITC_COMP,transition_point-1-slope_counter)
				sleep(0.01)
				sample_before = 0.0
				
				
				sample_before=GLITC.scaler_read(channel,sample_number,num_trials)-threshold_label+1

				#print "sample at: %1.2f" % sample_at
				#print "sample before: %1.2f" % sample_before
				#print threshold_label
				if (sample_before < 0.22  or sample_before > 0.78):
					"""(sample_at-0.05)"""
					inside_flag = False 
					if (slope_counter == 1):
						delta_minus += (sample_at-sample_before)
				else:
					delta_minus += (sample_at-sample_before)/float(slope_counter)
					slope_counter += 1
			
			delta_minus /= float(slope_counter) 
			
			if(bad_counter >= 10):
				delta_minus = 0.0001
				print "Bad Transition?"
				bad_slope_flag = 1
				break
			
			if(delta_minus==0): #The slope before should not be zero, because devideing by zero is bad! (sloping down!)
				print "Bad Counter %d" % bad_counter
				first_slope_flag=0
				bad_counter+=1
			else:
				first_slope_flag=1
			
			#first_slope_flag = 1
		print delta_minus
		#print "Starting Delta_plus loop"
		for j in range(-1,2):	
			#print j
			#New way to calculate delta_plus
			inside_flag = True #goes to False when outside range (0.5-0.22)
			slope_counter = 1 #this is the number of slopes that goes into calculating the avg slope
			delta_plus[j+1] = 0
			sample_lasttime = 0
			minimum_counter = 0
			while (inside_flag):
				sleep(0.01)	
				GLITC.rdac(RITC,RITC_COMP,transition_point-1+offset+j+slope_counter)
				sleep(0.01)
				if (offset+j == 0): #Protects us from situations where we are looking at the same point
					sample_after[j+1] = 10000.0
					delta_plus[j+1] += (sample_after[j+1]-sample_at)
					inside_flag = False
				else:
					sample_after[j+1] = 0
					#print slope_counter
					
					sample_after[j+1]=GLITC.scaler_read(channel,sample_number,num_trials)-threshold_label+1
					
					#print "sample at: %1.2f" % sample_at
					#print "sample after: %1.2f" % sample_after[j+1]
					if (sample_after[j+1] < 0.22 or sample_after[j+1] > 0.78 ):#(sample_at+0.05) ):
						inside_flag = False
						if (slope_counter == 1):
							delta_plus[j+1] += (sample_after[j+1]-sample_at)
					else:
						delta_plus[j+1] += (sample_after[j+1]-sample_at)/float(slope_counter)
						slope_counter+=1
						if (sample_lasttime == sample_after[j+1]):
							minimum_counter+=1
						if (minimum_counter >= 40):
							print "local plateau at %1.2f reached after %1.2f samples! moving on!" % (sample_after[j+1],slope_counter)
							break
						sample_lasttime = sample_after[j+1]
			delta_plus[j+1] /=float(slope_counter) 

			rms_error[j+1] = ((delta_plus[j+1]-delta_minus)/delta_minus)
				
		
		print delta_plus
		print offset
		print rms_error
		"""
		if(rough_offset > slope_counter):
			print "Slope counter %d" % slope_counter
			bad_slope_flag=1
			break
		"""
		if(np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[2]**2) and delta_plus[1]*delta_minus >=0):
			break
		elif (np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[2]**2) and delta_plus[1]*delta_minus <= 0):
			print "Slopes in opposite directions!"	
			bad_slope_flag = 1
			break
		elif(np.sqrt(rms_error[1]**2)>=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[0]**2)<=np.sqrt(rms_error[2]**2)):
			offset-=1
		elif(np.sqrt(rms_error[1]**2)>=np.sqrt(rms_error[2]**2) and np.sqrt(rms_error[2]**2)<=np.sqrt(rms_error[0]**2)):
			offset+=1
		if(offset<min_offset):
			offset=min_offset
			break
	return offset, rms_error, bad_slope_flag
	

def find_overlay_offset(GLITC,channel,threshold_label,sample_number,transition_point,scan_width=150,num_trials=100):
	#print "Starting overlay offset finder"
	RITC,RITC_COMP = get_channel_info(channel,threshold_label)
	
	
	sample_array = []
	threshold_array = []
	
	#offset = 0
	# Do fine threshold scan
	for thres_i in range(transition_point-scan_width,transition_point+scan_width):
		sample_temp = 0
		#print thres_i
		GLITC.rdac(RITC,RITC_COMP,thres_i)
		sleep(0.01)
		

		sample_temp = GLITC.scaler_read(channel,sample_number,num_trials)-threshold_label+1

		sample_array.append(sample_temp)
		threshold_array.append(thres_i)
		
		
		
	best_diff = 10000
	# Find best offset
	for offset_i in range(1,scan_width):
		diff = 0
		#print "Offset %d"%offset_i
		for thres_i in range(offset_i):
			if(sample_array[scan_width-thres_i-1]==0):
				sample_array[scan_width-thres_i-1]=0.00000001
			diff += np.sqrt(((sample_array[scan_width-thres_i-1]-sample_array[scan_width-thres_i+offset_i-1])/sample_array[scan_width-thres_i-1])**2)
			#print sample_array[scan_width-thres_i-1]
			#print threshold_array[scan_width-thres_i-1]
			#print sample_array[scan_width-thres_i+offset_i-1]
			#print threshold_array[scan_width-thres_i+offset_i-1]
		diff /=offset_i
		
		#print "Diff %f"%diff
		if(diff<best_diff):
			offset = offset_i
			best_diff = diff
			
			
	# Calculate the error
	rms_error = [0]*3	
	delta_plus = [0]*3
	avg_diff = [0]*3	
	delta_minus = 0
	inside_flag = True #goes to False when outside range (0.5-0.78)
	slope_counter = 1 #this is the number of slopes that goes into calculating the avg slope
	sample_at = sample_array[scan_width-1]
	
	while (inside_flag):
		sample_before = sample_array[scan_width-1-slope_counter]
		#print "sample at: %1.2f" % sample_at
		#print "sample before: %1.2f" % sample_before
		#print threshold_label
		if (sample_before < 0.22  or sample_before > 0.78):
			inside_flag = False 
			if (slope_counter == 1):
				delta_minus += (sample_at-sample_before)
				if (delta_minus == 0):
					delta_minus = 0.000000001
		else:
			delta_minus += (sample_at-sample_before)/float(slope_counter)
			slope_counter += 1
	delta_minus /= float(slope_counter) 
	
	# Find rms_errors around best offset	
	for i in range(-1,2):
		print "Offset %d" % (offset+i)
		for thres_i in range(offset+i):
			avg_diff[i+1] += np.sqrt(((sample_array[scan_width-thres_i-1]-sample_array[scan_width-thres_i+offset+i-1])**2))
			#rms_error[i+1] += np.sqrt(((sample_array[scan_width-thres_i-1]-sample_array[scan_width-thres_i+offset+i-1])/sample_array[scan_width-thres_i-1])**2)
		avg_diff[i+1] /=offset_i
		delta_plus[i+1] = (avg_diff[i+1] + abs(delta_minus))
		rms_error[i+1] = (delta_plus[i+1]-abs(delta_minus))/abs(delta_minus)
		
	print offset
	print rms_error
	return offset, rms_error[0],rms_error[1],rms_error[2]

	
def find_best_offset(GLITC,channel,threshold_label,sample_number,sample_array,transition_point,transition_value_index,num_trials=100):
	rms_error = [0]*3
	# Try out different offsets and see which one is the closest match
	rough_offset = find_rough_offset(sample_array,transition_value_index)
	"""
	offset=1
	sample_before_transition = sample_array[transition_value_index-1]
	#print transition_value_index
	#print "Sample before transition %f" % sample_before_transition
	#print sample_array[transition_value_index-10:transition_value_index+10]
	for i in range(transition_value_index,len(sample_array)):
		#print "Test_sample %f"%(sample_array[i])
		if(sample_array[i]<sample_before_transition):
			offset = i-transition_value_index
			break
	"""
	# Now that we have a rough estimate of the offset
	# Take extra data around the transition point-1 and the transmision point-1+offset
	offset, rms_error,bad_slope_flag = find_slope_offset(GLITC,channel,threshold_label,sample_number,transition_point,rough_offset,num_trials=num_trials)
	offset_method = "slope"
	
	#bad_slope_flag = 1
	# If the slope method failed, use the overlay method
	if(bad_slope_flag):
		print "Slope finder failed, running overlay finder"
		offset, rms_error[0],rms_error[1],rms_error[2] = find_overlay_offset(GLITC,channel,threshold_label,sample_number,transition_point,num_trials=num_trials)
		offset_method = "overlay"

	
	return offset,rough_offset,rms_error[0],rms_error[1],rms_error[2], offset_method
	
	
def transition_threshold_scan(GLITC,GLITC_n,channel,RITC,RITC_COMP,input_dac_transition_value,transition_value,threshold_label,sample_number,pp,num_trials=10,wait_time=0.01):
	sample_value_array = np.zeros(32)

	offset_flag = 0
	previous_sample = 1.0
	offset=0
	threshold_array = []
	sample_array = []
	inside_flag = 0
	outside_flag = 1
	midpoint_counter = 0
	
	for thres_i in range(transition_value-300,transition_value+300):
		#print "Setting threshold to %1.1d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
		# Step threshold dac value
		GLITC.rdac(RITC,RITC_COMP,thres_i)
		sleep(wait_time)

		sample_value = 0.0
		# Read in samples and check if it passes the sample transition point
		sample_value = GLITC.scaler_read(channel,sample_number,num_trials)
		
		"""
		if(sample_value>=0.4 and sample_value<=0.6 and inside_flag!=1):
			#print "Entering acceptable range"
			#print sample_value
			#print thres_i
			inside_flag = 1
			outside_flag = 0
			midpoint_counter+=1
		if((sample_value<0.4 or sample_value>0.6) and outside_flag!=1):
			#print "Exiting acceptable range"
			#print sample_value
			#print thres_i
			inside_flag = 0
			outside_flag = 1
			midpoint_counter+=1
		"""
		threshold_array.append(thres_i)
		sample_array.append(sample_value)
		if (thres_i == transition_value):
			transition_value_index = len(sample_array)-1

	#if(midpoint_counter<5):
	make_scatter_plot(pp,threshold_array,sample_array,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,1)	
	
	return threshold_array,sample_array,transition_value_index


def vss_scan(GLITC_n,channel,input_dac_transition_value=800,num_scans=4,vss_min=1300,vss_max=1800,threshold_label=4,sample_number=0,pp=None,num_trials=10,wait_time=0.01):
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
	
	GLITC = setup(GLITC_n)
	
	GLITC.reset_all_thresholds(RITC,0)
	
	# Set higher threshold to maximum
	for threshold_level_ii in range(0,7-threshold_label):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
	
	transition_value = int(input_dac_transition_value*2500./1200.)#-200
	print "Setting input dac to %d" % input_dac_transition_value
	GLITC.dac(channel,input_dac_transition_value)
	sleep(5)
	
	colors = iter(cm.brg(np.linspace(0,1,num_scans)))
	plt.figure(figsize=(16,12))	
	vss = np.linspace(vss_min,vss_max,num_scans)
	
	print "RITC %d" % RITC
	print "RITC COMP %d" % RITC_COMP
	for scan_i in range(num_scans):
		print scan_i

		threshold_array = []
		sample_array = []	
		
		"""
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		"""
		GLITC.rdac(RITC,31,int(vss[scan_i]))
		sleep(wait_time)
		"""
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
		"""
		for thres_i in range(transition_value-450,transition_value+450):
			#print "Setting threshold to %d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
			# Step threshold dac value
			GLITC.rdac(RITC,RITC_COMP,thres_i)
			sleep(wait_time)

			sample_value = 0.0
			# Read in samples and check if it passes the sample transition point

			sample_value = GLITC.scaler_read(channel,sample_number,num_trials)

			
			threshold_array.append(thres_i)
			sample_array.append(sample_value)

		plt.plot(threshold_array,sample_array,color=next(colors),label=("Vss: %d" % vss[scan_i]))
		#make_scatter_plot(pp,threshold_array,sample_array,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,1)	
	plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Sample Number "+str(sample_number))
	plt.xlabel("Threshold Voltage (DAC Counts)")
	plt.ylabel("Normalized Output Value")
	plt.legend()
	plt.text(transition_value*1.02,threshold_label*1.01, ('Input DAC: %1.1d' % input_dac_transition_value), fontsize = 18)
	#plt.axis([transition_value-150,transition_value+150,2.8,7])
	#plt.savefig('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/timing_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_sample'+str(sample_number)+'_vss_study_6')
	plt.show()
	#return threshold_array,sample_array,transition_value_index,midpoint_counter
	return 0


def vdd_scan(GLITC_n,channel,input_dac_transition_value=800,num_scans=4,vdd_min=2000,vdd_max=4000,threshold_label=4,sample_number=0,pp=None,num_trials=10,wait_time=0.01):
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
	
	GLITC = setup(GLITC_n)
	
	GLITC.reset_all_thresholds(RITC,0)
	
	# Set higher threshold to maximum
	for threshold_level_ii in range(0,7-threshold_label):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
	
	transition_value = int(input_dac_transition_value*2500./1200.)#-200
	print "Setting input dac to %d" % input_dac_transition_value
	GLITC.dac(channel,input_dac_transition_value)
	sleep(5)
	
	colors = iter(cm.brg(np.linspace(0,1,num_scans)))
	plt.figure(figsize=(16,12))	
	vdd = np.linspace(vdd_min,vdd_max,num_scans)
	
	print "RITC %d" % RITC
	print "RITC COMP %d" % RITC_COMP
	for scan_i in range(num_scans):
		print scan_i

		threshold_array = []
		sample_array = []	
		
		"""
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		"""
		GLITC.rdac(RITC,32,int(vdd[scan_i]))
		sleep(wait_time)
		"""
		GLITC.training_ctrl(1)
		sleep(wait_time)
		GLITC.eye_autotune_all()
		sleep(wait_time)
		GLITC.training_ctrl(0)
		sleep(wait_time)
		"""
		for thres_i in range(transition_value-450,transition_value+450):
			#print "Setting threshold to %d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
			# Step threshold dac value
			GLITC.rdac(RITC,RITC_COMP,thres_i)
			sleep(wait_time)

			sample_value = 0.0
			# Read in samples and check if it passes the sample transition point
			sample_value = GLITC.scaler_read(channel,sample_number,num_trials)

			
			threshold_array.append(thres_i)
			sample_array.append(sample_value)

		plt.plot(threshold_array,sample_array,color=next(colors),label=("Vdd: %d" % vdd[scan_i]))
		#make_scatter_plot(pp,threshold_array,sample_array,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,1)	
	plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Sample Number "+str(sample_number))
	plt.xlabel("Threshold Voltage (DAC Counts)")
	plt.ylabel("Normalized Output Value")
	plt.legend()
	plt.text(transition_value*1.02,threshold_label*0.95, ('Input DAC: %1.1d' % input_dac_transition_value), fontsize = 18)
	#plt.axis([transition_value-150,transition_value+150,2.8,7])
	#plt.savefig('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/timing_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_sample'+str(sample_number)+'_vdd_study')
	plt.show()
	#return threshold_array,sample_array,transition_value_index,midpoint_counter
	return 0


def input_dac_scan(GLITC,GLITC_i,channel_i,dac_min=500,dac_max=1000,dac_step = 10,num_trials=10,wait_time=0.01):
	
	sample_value_array = np.zeros(32)

	offset_flag = 0
	previous_sample = 1.0
	offset=0
	input_array = []
	sample_array = []

	for input_i in range(dac_min,dac_max+1,dac_step):
		#print "Setting threshold to %1.1d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
		# Step threshold dac value
		print "Setting input to: %d" % input_i
		GLITC.dac(channel_i,input_i)
		sleep(5)

		#sample_value = 0.0
		# Read in samples and check if it passes the sample transition point
		sample_value = GLITC.scaler_read_all(channel_i,num_trials)
		"""
		if(sample_value>=0.4 and sample_value<=0.6 and inside_flag!=1):
			inside_flag = 1
			outside_flag = 0
			midpoint_counter+=1
		if((sample_value<0.4 or sample_value>0.6) and outside_flag!=1):
			inside_flag = 0
			outside_flag = 1
			midpoint_counter+=1
		"""
		input_array.append(input_i)
		sample_array.append(sample_value)
	
	sample_array = np.transpose(sample_array)
	return sample_array,input_array


def board_sample_scan(input_dac_value=800,threshold_label=4,num_trials=10,wait_time=0.01):
	for GLITC_n in range(4):
		for channel in range(7):
			if(channel==3):
				continue
			pp = PdfPages('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/sample_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_sample_study_2.pdf')
			sample_scan(GLITC_n,channel,input_dac_value,threshold_label,pp,num_trials,wait_time)
			pp.close()


def sample_scan(GLITC_n,channel,input_dac_value=800,threshold_label=4,pp=None,num_trials=10,wait_time=0.01):
	
	transition_value = int(input_dac_value*2500./1200.)#-200
	max_threshold = transition_value+500
	min_threshold = transition_value-100
	threshold_step = 1
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
	
	GLITC = setup(GLITC_n)
	
	GLITC.reset_all_thresholds(RITC,0)
	
	# Set higher threshold to maximum
	for threshold_level_ii in range(0,7-threshold_label):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
	
	
	print "Setting input dac to %d" % input_dac_value
	GLITC.dac(channel,input_dac_value)
	sleep(5)
	
	
	f1 = plt.figure(1,figsize=(16,12))
	if(pp!=None):
		f2 = plt.figure(2,figsize=(16,12))	
	colors = iter(cm.brg(np.linspace(0,1,32)))
	
	print "RITC %d" % RITC
	print "RITC COMP %d" % RITC_COMP
	
	threshold_array = []
	sample_array = []
	color = []
	"""
	for thres_i in range(transition_value-100,transition_value+500):
		if(int(thres_i) % 100 == 0):
			print "Setting threshold to %d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
		# Step threshold dac value
		GLITC.rdac(RITC,RITC_COMP,thres_i)
		sleep(wait_time)
		
		sample_value = []
		#threshold_value = []
			
		sample_value = GLITC.scaler_read_all(channel,num_trials)
		#threshold_value = [thres_i]*32
			
		sample_array.append(sample_value)
		threshold_array.append(thres_i)

	sample_array = np.transpose(sample_array)
	#threshold_array = np.transpose(threshold_array)
	"""
	sample_array,threshold_array = threshold_scan_all_samples(GLITC,GLITC_n,channel,threshold_label,num_trials,min_threshold,max_threshold,threshold_step,wait_time)
	
	print "Plotting samples"
	for sample_i in range(32):	
		#print "Plotting sample %d" % sample_i
		color.append(next(colors))
		plt.figure(1)
		plt.plot(threshold_array,sample_array[sample_i],color=color[sample_i],label=("Sample: %d" % sample_i))
		plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Input: "+str(input_dac_value))
		plt.xlabel("Threshold Voltage (DAC Counts)")
		plt.ylabel("Normalized Output Value")
		plt.legend()
		#plt.text(transition_value*1.02,threshold_label*1.01, ('Input DAC: %1.1d' % input_dac_transition_value), fontsize = 18)
		#plt.axis([transition_value-150,transition_value+150,2.8,7])
		
		
		if(pp!=None):
			#print "trying to make pdf"
			plt.figure(2)
			plt.clf()
			plt.plot(threshold_array,sample_array[sample_i],color=color[sample_i],label=("Sample: %d" % sample_i))
			plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Input: "+str(input_dac_value))
			plt.xlabel("Threshold Voltage (DAC Counts)")
			plt.ylabel("Normalized Output Value")
			plt.legend()
			plt.savefig(pp, format='pdf')
	
	plt.figure(1)
	plt.show()
	#plt.savefig('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/sample_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_input'+str(input_dac_value)+'_2.png')
	plt.close()
	if(pp!=None):
		plt.figure(2)
		plt.close()
	return 0

# Take in a dac value and calculate the corrected dac value
def stitch_threshold_dac(GLITC_n,channel,RITC_DAC_Number,dac):
	dac_temp = dac
	
	"""
	offset_2048 = 0#89
	offset_1024 = 0#41
	offset_512 = 0#19
	offset_256 = 0#9
	offset_128 = 0 
	"""
	offset_2048,offset_1024,offset_512,offset_256,offset_128 = tod.get_offsets(TISC,GLITC_n,channel,RITC_DAC_Number)
	total_offset = offset_2048+offset_1024+2*offset_512+4*offset_256+8*offset_128
	if(dac>2047-total_offset):
		dac+=total_offset
		dac_temp-=2048+total_offset
		
	total_offset = offset_1024+offset_512+2*offset_256+4*offset_128
	if(dac_temp>1023-total_offset):
		dac+=total_offset
		dac_temp-=1024+total_offset
	
	total_offset = offset_512+offset_256+2*offset_128
	if(dac_temp>511-total_offset):
		dac+=total_offset
		dac_temp-=512+total_offset
	
	total_offset = offset_256+offset_128
	if(dac_temp>255-total_offset):
		dac+=total_offset
		dac_temp-=256+total_offset
	
	total_offset = offset_128
	if(dac_temp>127-total_offset):
		dac+=total_offset
		dac_temp-=128+total_offset
	return dac
	
#execute threshold scan inorder to plot a histogram
def threshold_plotter():

	wait_time = .01
	

	sample_values = []

	for i in range(32):
		sample_values.append([])


	starttime = time()
	for GLITC_n in range(1):
	
		# Setup the GLITC
		setup(GLITC_n)
	
		print "Starting threshold/pedistal scan on GLITC "+str(GLITC_n)

		#loop over each channel, note our channel here goes left to right on the board.
		for channel_i in range(1):#,7):
			if (channel_i==3):
				continue
			if (channel_i <= 2):
				RITC = 0
			elif (channel_i >2):
				RITC = 1
			
			#datafile = open('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/Fine/channel_'+str(channel_i)+'_threshold_data_ultrafine.dat','w')
			#datafile.write('GLITC,Channel,Threshold_DAC,Threshold_dac_value,Pedestal_dac_value,sample_values_0_to_31\n')
			#with open('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/channel_'+str(channel_i)+'_threshold_data_stiched_dac.dat','wb') as f:
				#writer = csv.writer(f)
				#writer.writerow(['trial_number','glitc','channel','threshold_dac','threshold_dac_value','input_dac_value','sample_0_21'])
				#pp = PdfPages('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/test_GLITC_'+str(GLITC_n)+'_Ch_'+str(channel_i)+'_hist.pdf')

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
						#plt.savefig(("TISC%d/GLITC_%1.1d/plots/Ch_%1.1d/ch_%1.1d_ped_%1.1d.png") % (TISC,int(GLITC),int(channel), int(channel), (int(pedestal_value[row_i-2]))*2500.0/4095.0))
						if(pp!=None):
							plt.savefig(pp, format='pdf')
						plt.show()
						plt.clf()
						plt.close()
		
						
						#set this threshold level threashold back to zero (highest threshold) before moving to the next.
						#GLITC.rdac(RITC,RITC_COMP,0)
					sleep(wait_time)
				if(pp!=None):
					pp.close()
				#datafile.close()
	stoptime = time()
	print "Stopped at: "+str(stoptime)
	print "Took: "+str(stoptime-starttime)

#fit the data from a scan and create a histogram while saving information
def threshold_polyfit():
		
	for GLITC_i in range(4):
		for channel_i in range(7):
			
			
			
			for threshold_label in range(1,7+1):
				
				header_flag = 0
				input_dac = []
				threshold_dac = []
				output = []
				output_temp = []
				mean_temp = []
				sigma_temp = []
				input_temp = []
				
				with open('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_2.dat'%(TISC,GLITC_i,GLITC_i,channel_i,threshold_label),'rb') as datafile:
					datareader = csv.reader(datafile, delimiter=',', quotechar='|')
					for row in datareader:
						# First row is header
						if (header_flag == 0):
							header = row
							header_flag = 1
							print "This is the header"
						# Gather all data
						else:
							
							output_temp.append(float(row[3]))
							sample_number = int(row[2])
							print len(output_temp)	
							# Seperate each block of 32 samples
							if(sample_number == 31):
								
								#print len(output_temp)	
								input_dac.append(int(row[0]))
								threshold_dac.append(int(row[1]))
								output.append(output_temp)
								
								# Reset temp arrays
								print "Resetting arrays"
								output_temp = []
						
				
				datafile.close()
				
				# Make first indice the sample number
				print len(output[:,0])
				output = np.transpose(output)
				print len(output[:,0])
				print output.shape
				
				input_test = input_dac[0]
				# Find number of input points per scan & number of scans
				for i in range(len(input_dac)):
					if(input_dac[i]!=input_test):
						num_input_points_per_scan = i+1
						num_scans = int(len(input_dac)/num_input_points)
						input_step = input_dac[i]-input_test
						break
				
				output_under_test = [0]*num_input_points_per_scan
				threshold_dac_under_test = [0]*num_input_points_per_scan
				
				# Goofy stuff to only use one input scan at a time
				for scan_i in range(num_scans):
					start_index = scan_i*num_input_points_per_scan
					end_index = start_index+num_input_points_per_scan-1
					
					# Picking off the data from a single input scan
					threshold_dac_under_test = threshold_dac[start_index:end_index]
					output_under_test = output[:,start_index:end_index]
					
					# Find transition point
					transition_point = [0]*32
					for input_i in range(num_input_points_per_scan):
						for sample_i in range(32):
							for i in range(len(output_under_test[sample_i])):
								if(output_under_test[sample_i][i]<threshold_label-0.5):
									transition_point[sample_i] = threshold_dac_under_test[i]
									break
						
					# Fit data with gaussian and get mean and sigma
					bin_range = [min(threshold_dac[0]),max(threshold_dac[0])]
					bin_width = 20
					bin_num = int((bin_range[1]-bin_range[0])/bin_width)
					bc_sigma = (1.0/np.sqrt(12))*float(bin_width)
					(mu, sigma) = norm.fit(transition_point)
					full_sigma = np.sqrt(sigma**2+bc_sigma**2)
					input_temp.append(input_dac[start_index])
					
					# If histogram is good, save information
					if(full_sigma <= 100):
						mean_temp.append(mu)
						sigma_temp.append(full_sigma)
						
						
					# If histogram is bad, set everything to zero
					else:
						mean_temp.append(0)
						sigma_temp.append(0)
						
				# Close goofy for loop		
				print mean_temp
				print sigma_temp	
						
				# Collect all mean and sigma arrays
				#mean.append(mean_temp)
				#sigma.append(sigma_temp)


#find threshold offsets for all the things, generate files that make_threshoold_offset_dictionary will use.
def find_threshold_offsets():

	wait_time = 0.01

	transition_values = [2048,1024,1536,1792]
	
	sample_number = 0
	for GLITC_n in range(4):

		GLITC = setup(GLITC_n)
		
		for channel in range(7):
			if (channel ==3):
				continue

			if (channel <= 2):
				RITC = 0
			elif (channel >2):
				RITC = 1
			
			# Reset all threshold to minimum
			print "Setting all thresholds to minimum"
			GLITC.reset_all_thresholds(RITC,0)
			
			with open('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/transition_study/GLITC_'+str(GLITC_n)+'_channel_'+str(channel)+'_transition_offsets_1.dat','wb') as f:
				writer = csv.writer(f)
				writer.writerow(['GLITC','channel','threshold_dac_number','threshold_label','transition','input_dac_value','sample_number','offset','rough_offset','previous_rms_error','rms_error','next_rms_error','clean_transition_flag'])
				pp = PdfPages('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/transition_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_transitions_1.pdf')
			#if(True):	
				
				#pp = None
				for threshold_level_i in range(7):
					threshold_label = 7-threshold_level_i
					
					
					# Get the DAC numbers

					RITC,RITC_COMP = get_channel_info(channel,threshold_label)
					
					# Set higher threshold to maximum
					for threshold_level_ii in range(0,threshold_level_i):
						print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
						GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
					
					
					### Take data from board ###########################
					for i in range(len(transition_values)):
						transition_value = transition_values[i]
						sample_number = 0
						clean_transition_flag = 0
						"""
						if(transition_value ==2048 and threshold_level_i>=2):
							continue
						elif(transition_value == 1024 and threshold_level_i<=4):
							continue
						"""	
						
						#while(clean_transition_flag!=1):
						input_dac_transition_value,sample_transition_value,sample_number = find_bit_transition_all_samples(GLITC,GLITC_n,channel,RITC,RITC_COMP,transition_value,threshold_label,sample_number,pp)
						"""
						input_dac_transition_value=637
						sample_transition_value = 0.5
						sample_number=0
						GLITC.dac(channel,input_dac_transition_value)
						sleep(5)
						"""
						sample_value_array = np.zeros(32)
						sample_value = 0.0
						
						offset_flag = 0
						previous_sample = 1.0
						offset=0
						threshold_array = []
						sample_array = []
											
						graph_3_x = []
						graph_3_y = []
						
						threshold_array,sample_array,transition_value_index = transition_threshold_scan(GLITC,GLITC_n,channel,RITC,RITC_COMP,input_dac_transition_value,transition_value,threshold_label,sample_number,pp)
						"""
						print midpoint_counter
						if(midpoint_counter>4):
							clean_transition_flag = 0
							#if(sample_number<31):
								#sample_number+=1
							#else:
								#sample_number = 0
							#print "Too many midpoint crossings, moving to sample %d" % sample_number
							#continue
						else:
							clean_transition_flag = 1
						"""	
						offset,rough_offset,previous_rms_error,rms_error,next_rms_error,offset_method = find_best_offset(GLITC,channel,threshold_label,sample_number,sample_array,transition_value,transition_value_index)
							
						
						
						graph_3_x = []
						graph_3_y = []
						
						
						for thres_i in range(len(sample_array)-offset):
							#print "Setting threshold to %1.1d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
							# Step threshold dac value
							if(threshold_array[thres_i]>=transition_value):

								graph_3_x.append(threshold_array[thres_i])
								graph_3_y.append(sample_array[thres_i+offset])
							else:
								graph_3_x.append(threshold_array[thres_i])
								graph_3_y.append(sample_array[thres_i])
						
						print "\nGLITC %d, Channel %1.1d, threshold %1.1d, offset %1.1d (%1.2fmV) for %1.1d transition\n" % (GLITC_n,channel, threshold_label,offset, offset*1200./4095.,transition_value)
						writer.writerow([GLITC_n,channel,RITC_COMP,threshold_label,transition_value,input_dac_transition_value,sample_number,offset,rough_offset,previous_rms_error,rms_error,next_rms_error,offset_method])

					####################################################
					
						
						make_scatter_plot(pp,graph_3_x,graph_3_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,offset,sample_number,2)
				
				if(pp!=None):
					pp.close()
					
	return None


#plot the threshold data, also make data files that make_threshold_setting_dictionary uses			
def threshold_transition_scanner():
	
	min_input = 400
	max_input = 1400
	step_input = 40
	num_input_steps = int((max_input-min_input)/step_input)+1
	input_array = [0]*num_input_steps

	min_threshold_range = 900
	max_threshold_range = 3500 
	threshold_step = 10
	num_trials = 1

	input_midpoint = 760

	file_iterator = "3"

	for GLITC_i in range(2):
		
		GLITC = setup(GLITC_i)
		
		for channel_i in range(7):
			
			mean_array = [0]*num_input_steps
			sigma_array = [0]*num_input_steps
			counter_array = [0]*num_input_steps
			input_array = [0]*num_input_steps
			working_range_start_flag = 0
			
			if (channel_i==3): continue
		
			for threshold_level_i in range(7):
				threshold_label = 7-threshold_level_i
				print "\nStarting GLITC %d, Ch %d, Threshold %d\n"%(GLITC_i,channel_i,threshold_label)
				pp = PdfPages('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_transition_histogram_%s.pdf'%(TISC,GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator))
				ppp = PdfPages('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_transition_line_%s.pdf'%(TISC,GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator))
				
				RITC,RITC_COMP = get_channel_info(channel_i,threshold_label)
				GLITC.reset_all_thresholds(RITC,0)
				
				# Set higher threshold to maximum
				for threshold_level_ii in range(0,threshold_level_i):
					print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
					GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
							
				with open('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_%s.dat'%(TISC,GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator),'wb') as f:
					writer = csv.writer(f)
					writer.writerow(['Input_DAC','Threshold_DAC','Sample Output'])
				#if(True):
					#pp = None
					#ppp = None
					
					threshold_transition_mean = []
					threshold_transition_sigma = []
					input_array_temp = []
									
					
					with open('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_bad_sample_%s.dat'%(TISC,GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator),'wb') as f:
						writer2 = csv.writer(f)
						writer2.writerow(['Input_DAC','Bad Samples'])
					
						for input_dac_i in range(min_input,max_input+1,step_input):
							colors = iter(cm.brg(np.linspace(0,1,32)))
		
							print "Setting input DAC to %d (%1.2f mV)" % (input_dac_i,input_dac_i*2500./4095.)
							GLITC.dac(channel_i,input_dac_i)
							sleep(5)
							
							print "Starting threshold scan"
							sample_array,threshold_array = threshold_scan_all_samples(GLITC,GLITC_i,channel_i,threshold_label,num_trials,min_threshold_range,max_threshold_range,threshold_step)
			
							# Write all data to file
							for i in range(len(sample_array[0])):
								write_array = []
								write_array.append(input_dac_i)
								write_array.append(threshold_array[i])
								for sample_i in range(32):
									write_array.append(sample_array[sample_i][i])
								writer.writerow(write_array)
					
						
							transition_point = [0]*32
							plt.figure(figsize=(16,12))
							print "Making threshold plots"
							for sample_i in range(32):
								
								plt.plot(threshold_array,sample_array[sample_i],color=next(colors),label=("Sample %d"%sample_i))
								
								for i in range(len(sample_array[sample_i])):	
									if(sample_array[sample_i][i]<threshold_label-0.5):
										transition_point[sample_i] = threshold_array[i]
										break
						
							#remove samples that are never good, but also samples that went bad...
							#this is just to help with fitting the transition_point array 
							bad_sample_index_array = []
							for sample_i in range(32):
								if (transition_point[sample_i] < min_threshold_range or transition_point[sample_i] > max_threshold_range):
									bad_sample_index_array.append(sample_i)
							write_array2 = []
							write_array2.append(input_dac_i)
							write_array2.append(bad_sample_index_array)
							writer2.writerow(write_array2)
							
							#we also dont want to fit a normal distribution to just a few sample transition
							if (len(bad_sample_index_array) == 0 or len(bad_sample_index_array) >= 10):
								good_transition_point = transition_point
							else:
								good_transition_point = np.delete(transition_point, bad_sample_index_array, None)

						
								
							plt.title("GLITC %d,Channel %d,Threshold %d, Input %d"%(GLITC_i,channel_i, threshold_label,input_dac_i))
							plt.xlabel("Threshold_DAC")
							plt.ylabel("Output Value")
							plt.legend(loc='center left',bbox_to_anchor=(0.9,0.5))
							#plt.show()
							plt.savefig(ppp,format='pdf')
							plt.clf()	
							plt.close()
						
							plt.figure(figsize=(16,12))
							print "Making histograms"
							bin_range = [min_threshold_range,max_threshold_range]
							bin_width = 2*threshold_step
							bin_num = int((bin_range[1]-bin_range[0])/bin_width)
							#bc_sigma = (1.0/np.sqrt(12))*float(bin_width)
							

							(mu, sigma) = norm.fit(good_transition_point)
							full_sigma = sigma#np.sqrt(sigma**2+bc_sigma**2)
							plt.hist(transition_point,bin_num,range=bin_range,label=('Input DAC: %d, $\mu=%1.4f, \sigma=%1.4f$' % (input_dac_i,mu,full_sigma)))
	
							plt.xlabel("Threshold DAC")
							plt.ylabel("Counts")
							plt.title("GLITC "+str(GLITC_i)+", Ch "+str(channel_i)+", Threshold "+str(threshold_label)+" Transition Histogram")
							plt.text(550,4, (r'$Bin\ width = %1.1d $' % bin_width), fontsize = 20)
							plt.legend()
							#plt.show()
							plt.savefig(pp, format='pdf')
							plt.clf()
							plt.close()
						
						
							if(full_sigma<=100 and mu>(min_threshold_range+100)):
								threshold_transition_mean.append(mu)
								threshold_transition_sigma.append(full_sigma)
								input_array_temp.append(input_dac_i)
								if(threshold_label==1 and working_range_start_flag!=1):
									working_range_start = input_dac_i
									working_range_start_flag = 1
								#elif(threshold_label==7):
									#working_range_end = input_dac_i
							
							else:
								threshold_transition_mean.append(0)
								threshold_transition_sigma.append(0)
								input_array_temp.append(0)
							good_end_flag = 0
							if(threshold_label==7 and full_sigma<=200):
									working_range_end = input_dac_i
									good_end_flag = 1
							elif(threshold_label==7 and full_sigma<=300 and good_end_flag == 0 ):
									working_range_end = input_dac_i

					pp.close()
					ppp.close()
					#writer.close()	
			
				print "Threshold transition mean"+str(threshold_transition_mean)
				print "Threshold transition sigma"+str(threshold_transition_sigma)
			
				mean_array = np.add(mean_array,threshold_transition_mean)
				sigma_array = np.add(sigma_array,threshold_transition_sigma)
				input_array = np.add(input_array,input_array_temp)
				for i in range(len(threshold_transition_mean)):
					if(threshold_transition_mean[i]!=0):
						counter_array[i]+=1

			print "Mean array"+str(mean_array)
			print "Sigma array"+str(sigma_array)
			print "Counter array"+str(counter_array)
			
			# Trim any zeros from the arrays
			mean_array = np.trim_zeros(mean_array)
			sigma_array = np.trim_zeros(sigma_array)
			input_array = np.trim_zeros(input_array)
			counter_array = np.trim_zeros(counter_array)
			#but trim doesn't tke care of non-edge zeros, we need those gone too.
			zero_index_array = []
			for i in range(len(mean_array)):
				if counter_array[i] == 0:
					zero_index_array.append(i)		
			if len(zero_index_array) != 0:
				mean_array = np.delete(mean_array, zero_index_array, None)
				sigma_array = np.delete(sigma_array, zero_index_array, None)
				input_array = np.delete(input_array, zero_index_array, None)
				counter_array = np.delete(counter_array, zero_index_array, None)
			# Mean the mean and sigma arrays for the entire channel			
			mean_array = np.divide(mean_array,counter_array)
			sigma_array = np.divide(sigma_array,counter_array)
			input_array = np.divide(input_array,counter_array)	
			
			

			# Now fit the mean array with a quadratic
			mean_fit = np.polyfit(input_array,mean_array,2)	
			if(mean_fit[0]>=0):
				mean_fit = np.concatenate([[0],np.polyfit(input_array,mean_array,1)])
				
			print "GLITC %d, Channel %d Fit Parameters" % (GLITC_i,channel_i)
			print "Fit "+str(mean_fit)
			
			#force symmetry around working rane midpoint
			if(working_range_end-input_midpoint<=input_midpoint-working_range_start):
				delta_working_range = working_range_end-input_midpoint
				working_input_range = np.linspace(input_midpoint-delta_working_range,working_range_end,7)
			else:
				delta_working_range = input_midpoint-working_range_start
				working_input_range = np.linspace(working_range_start,input_midpoint+delta_working_range,7)
			
			print "Working input range "+str(working_input_range)
			threshold_settings = [0]*7
			for threshold_i in range(7):
				threshold_label = 7-threshold_i
				threshold_settings[threshold_i] = mean_fit[0]*working_input_range[threshold_i]**2+mean_fit[1]*working_input_range[threshold_i]+mean_fit[2]
				
			print "Threshold settings "+str(threshold_settings)
				
			with open('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_settings_%s.dat'%(TISC,GLITC_i,GLITC_i,channel_i,file_iterator),'wb') as f:
					writer = csv.writer(f)
					writer.writerow(['GLITC','Channel'])
					writer.writerow([GLITC_i,channel_i])
					writer.writerow(['Input range'])
					writer.writerow(working_input_range)
					writer.writerow(['Fit parameters [a,b,c] for ax^2+bx+c'])
					writer.writerow(mean_fit)
					writer.writerow(['Threshold settings'])
					writer.writerow(threshold_settings)

#create a threshold loop for each channel on the GLITC that is being scanned
def threshold_loop():

	wait_time = .01

	sample_values = []

	for i in range(32):
		sample_values.append([])




	starttime = time()
	for GLITC_n in range(0,1):#:4):
		
		#setup GLITC
		setup(GLITC_n)
		
		print "Starting threshold/pedistal scan on GLITC "+str(GLITC_n)

		#loop over each channel, note our channel here goes left to right on the board.
		for channel_i in range(1,7):#,7):
			if (channel_i==3):
				continue
			if (channel_i <= 2):
				RITC = 0
			elif (channel_i >2):
				RITC = 1
		
			
			#datafile = open('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/Fine/channel_'+str(channel_i)+'_threshold_data_ultrafine.dat','w')
			#datafile.write('GLITC,Channel,Threshold_DAC,Threshold_dac_value,Pedestal_dac_value,sample_values_0_to_31\n')
			with open('/home/user/data/TISC%d/GLITC_'%TISC+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/channel_'+str(channel_i)+'_threshold_data_bit_1536_transition_test_long.dat','wb') as f:
				writer = csv.writer(f)
				writer.writerow(['trial_number','glitc','channel','threshold_dac','threshold_dac_value','input_dac_value','sample_0_21'])
				#loop over pedestal voltages
				for ped_i in range(700,710,10): 
					print "Pedestal voltage on channel "+str(channel_i)+" set to "+str(ped_i*2500/4095)+'mV'
					#print "RITC "+str(RITC)+", DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200/4095)+'mV'
					
					GLITC.dac(channel_i, ped_i)
					sleep(5)

					#Loop over threshold levels (0-6)
					for thres_level in range(4,5):
						
						
						#weird stuff with channel
						if (channel_i <= 2):
							RITC_COMP = (channel_i*7)+6-thres_level
						elif (channel_i >2):
							RITC_COMP = ((channel_i-4)*7)+6-thres_level

						# Reset all thresholds to the highest value
						reset_all_thresholds(GLITC,RITC)

									
						sevens_counter = 0
						
						min_threshold_range = int(1536-50.*4095./1200.) #int((4095.*(ped_i*2500./4095.-25.))/1200.)
						max_threshold_range = int(1536+50.*4095./1200.) #int((4095.*(ped_i*2500./4095.+100.))/1200.)
						#print min_threshold_range
						#print max_threshold_range
						
						#print (("Starting threshold %1.1d") % (RITC_COMP))
						#loop over threshold values
						for thres_i in range(min_threshold_range,max_threshold_range+1):
							print "RITC "+str(RITC)+", Threshold DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200./4095.)+'mV'
							
							GLITC.rdac(RITC,RITC_COMP,thres_i)
							sleep(wait_time)
							
							sample_values = []
							sample_values_temp = [0]*32

							for i in range(38):
								sample_values.append([])
							
							num_trials = 1000
							
							sample_values_temp = read_all_samples_n(GLITC, channel_i, num_trials)
							
							#for i in range(num_trials):
							sample_values[0].append(num_trials)
							sample_values[1].append(GLITC_n)
							sample_values[2].append(channel_i)
							sample_values[3].append(RITC_COMP)
							sample_values[4].append(thres_i)
							sample_values[5].append(ped_i)
							for j in range(32):
								sample_values[j+6].append(sample_values_temp[j]/float(num_trials))
								
							sample_values = np.transpose(sample_values)
						
						
							writer.writerows(sample_values)
							
							#print sample_values	 
				
							#datafile.write(('%1.1d,%1.1d,%2.2d,%4.4d,%4.4d') % (GLITC_n, channel_i,RITC_COMP,thres_i,ped_i))
							#average_value = 0
							#for i in range(32):
								#datafile.write(','+str(sample_values[i]))
								#average_value += sample_values[i]
							#datafile.write('\n')
							
							#average_value /= 32.0
							#if((average_value==0)):
								#sevens_counter +=1
							#else:
								#sevens_counter = 0
							#if(sevens_counter == 10):
								#print "Hit repeating point, moving to next threshold"
								#sevents_counter = 0
								#break
						
						#set this threshold level threashold back to zero (highest threshold) before moving to the next.
						#GLITC.rdac(RITC,RITC_COMP,0)
					sleep(wait_time)
				#datafile.close()
	stoptime = time()
	print "Stopped at: "+str(stoptime)
	print "Took: "+str(stoptime-starttime)

						
# Perform a threshold scan on one sample
def threshold_scan(GLITC,GLITC_n,channel,threshold_label,sample_number,num_trials=10,min_threshold_range=0,max_threshold_range=4095,threshold_step=30,wait_time=0.01):
	threshold_array = []
	sample_value_array = []
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
			
	for thres_i in range(min_threshold_range,max_threshold_range,threshold_step):
		#print ("RITC "+str(RITC)+", Threshold DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200./4095.)+'mV')	
		
		threshold_array.append(thres_i)
		thres_i = stitch_threshold_dac(GLITC_n,channel,RITC_COMP,thres_i)
		
		GLITC.rdac(RITC,RITC_COMP,thres_i)
		sleep(wait_time)
		
		sample_value = GLITC.scaler_read(channel,sample_number,num_trials)
		sample_value_array.append(sample_value)

	return sample_value_array,threshold_array
	
# Perform a threshold scan of all samples	
def threshold_scan_all_samples(GLITC,GLITC_n,channel,threshold_label,num_trials=10,min_threshold_range=0,max_threshold_range=4095,threshold_step=30,wait_time=0.01):
	
	threshold_array = []
	sample_array = []
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
			
	for thres_i in range(min_threshold_range,max_threshold_range+1,threshold_step):
		#print ("RITC "+str(RITC)+", Threshold DAC "+str(RITC_COMP)+" set to "+str(thres_i*1200./4095.)+'mV')	

		threshold_array.append(thres_i)
		thres_i = stitch_threshold_dac(GLITC_n,channel,RITC_COMP,thres_i)
		
		GLITC.rdac(RITC,RITC_COMP,thres_i)
		sleep(wait_time)
		
		sample_value = []
		sample_value = GLITC.scaler_read_all(channel,num_trials)
			
		sample_array.append(sample_value)


	sample_array = np.transpose(sample_array)
	
	return sample_array,threshold_array

# Scan the pedestal input and plot the result
def manual_offset_scan(GLITC,GLITC_n,channel,threshold_label,transition_value,input_dac,num_trials=100,min_threshold_range=0,max_threshold_range=4095,threshold_step=1,wait_time=0.01):

	colors = iter(cm.brg(np.linspace(0,1,32)))
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
	
	GLITC.reset_all_thresholds(RITC,0)
	
	threshold_level = 7-threshold_label
	plt.figure(figsize=(16,12))
	# Set higher threshold to maximum
	for threshold_level_i in range(0,threshold_level):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_i-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_i-1,4095)
		
	print "Setting input DAC to %d"%input_dac
	GLITC.dac(channel,input_dac)
	sleep(5)
	
	print "Scanning thresholds"
	sample_array,threshold_array = threshold_scan_all_samples(GLITC,GLITC_n,channel,threshold_label,num_trials,min_threshold_range,max_threshold_range,threshold_step,wait_time)
	
	print "Making plots"
	for sample_i in range(32):
		#make_scatter_plot(None,threshold_array,sample_array[sample_i],GLITC_n,channel,threshold_label,transition_value,input_dac,0,sample_i,1)
		
		plt.plot(threshold_array,sample_array[sample_i],color=next(colors),label=("Sample %d"%sample_i))
	#plt.legend()
	plt.title("GLITC %d, Channel %d, Threshold %d, Input %d"%(GLITC_n,channel,threshold_label,input_dac))
	plt.xlabel("Threshold DAC")
	plt.ylabel("Output Value")
	plt.show()
	return sample_array,threshold_array

# Used for reading output from a sine wave input	
def RITC_storage_sine_plotter(GLITC,GLITC_n,channel,ped_dac=730,atten_dac=0,input_amp_p2p=200.0,input_freq=400000000.0,num_reads=1):
	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	
	offsets = get_individual_sample_offsets(GLITC_n,channel)
	
	reload(tsd)
	print "Setting channel %d thresholds" % channel
	set_thresholds(GLITC,GLITC_n,channel)
	
	if(GLITC.dac(channel)!=ped_dac):
		sleep(0.01)
		GLITC.dac(channel,ped_dac)
		sleep(5)
		
	if(GLITC.atten(channel)!=atten_dac):
		sleep(0.01)
		GLITC.atten(channel,atten_dac)
		sleep(5)
	
	time = np.linspace(0,time_step*num_samples,num_samples)
	sample = GLITC.RITC_storage_read(channel,num_reads=num_reads*2)
	sleep(0.01)

	plt.figure(figsize=[16,12])
	#plt.plot(time[0:4*32-1],sample[0:4*32-1],label=('Digitized Output: %d MHz Sine Wave (%d mV P2P)'%(input_freq/1000000,input_amp_p2p)))
	plt.plot(time*10**9,sample,linestyle=':',label=('Digitized Output'))
	
	corrected_sample = sample
	
	for i in range(0,len(sample)-1):
		if(sample[i]==7 and sample[i+1]<=4):
			#print "Correcting down"
			corrected_sample[i] = 4

	corrected_sample = correct_individual_samples(sample,offsets)

	#plt.plot(time[0:4*32-1],corrected_sample[0:4*32-1],label=('Glitc corrected Digitized Output: %d MHz Sine Wave (%d mV P2P)'%(input_freq/1000000,input_amp_p2p)))
	plt.plot(time*10**9,corrected_sample,label=('Corrected Digitized Output'))
	#print sample
	#print corrected_sample
	"""
	#fitfunc = lambda p, x: p[0]*np.sin(2*np.pi*p[1]*x+p[2]) + p[3]
	#errfunc = lambda p, x, y: fitfunc(p,x) - y
	#p0 = [7.0,frequency[max_frequency_bin],0.0,3.5]
	#p1,success = leastsq(errfunc, p0[:], args=(time,sample))
	
	#plt.plot(time[0:4*32-1],fitfunc(p1,time)[0:4*32-1],label=('Fit: %d MHz Sine Wave (%d mV P2P)'%(p1[1]/1000000,2*abs(p1[0]*54.0))))
	"""
	
	plt.title("GLITC %d, Ch %d, Ped %d (%d mV), Atten %d (-%1.2f dB) - Input: %d MHz Sine Wave" % (GLITC_n,channel,ped_dac,ped_dac*2500/4095,atten_dac,atten_dac*0.25,input_freq/1000000))
	plt.xlabel("Time [ns]")
	plt.ylabel("Ouput Value")
	plt.legend()
	#plt.grid(True)
	plt.ylim((0,7))
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sine_study/%dMHz_sine_atten_%1.2fdB.png" % (TISC,GLITC_n,input_freq/1000000,atten_db)))
	plt.show()
	plt.close()
	
	corrected_sample_average = np.average(corrected_sample)
	print corrected_sample_average
	
	sample_fft = fft(corrected_sample-corrected_sample_average)
	frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
	max_frequency_bin = np.argmax(2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	print frequency[max_frequency_bin]
	
	plt.figure(figsize=[16,12])
	plt.axvline(x=input_freq,linestyle="--",color='r',label=("Input Frequency: %dMHz"%(input_freq/1000000)))
	plt.plot(frequency,2.0/num_samples*np.abs(sample_fft[0:num_samples/2]))
	#plt.ylim((0,2.5))
	plt.title("%d MHz Sine FFT"%(input_freq/1000000))
	plt.title("Impulse Test")
	plt.xlabel("Frequency [Hz]")
	plt.ylabel("Amplitude")
	plt.legend()
	plt.grid(True)
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sine_study/%dMHz_sine_fft_atten_%1.2fdB.png" % (TISC,GLITC_n,input_freq/1000000,atten_db)))
	plt.show()
	#plt.clf()
	#plt.close()
	del corrected_sample
	del sample
	
	return None
	
# Used for reading output from an impulsive input
def RITC_storage_impulse_only(GLITC,GLITC_n,channel,ped_dac=730,atten_dac=0,input_amp_p2p=200.0,num_reads=1):
	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	
	reload(tsd)
	print "Setting channel %d thresholds" % channel
	set_thresholds(GLITC,GLITC_n,channel)
	
	if(GLITC.dac(channel)!=ped_dac):
		sleep(0.01)
		GLITC.dac(channel,ped_dac)
		sleep(5)
		
	if(GLITC.atten(channel)!=atten_dac):
		sleep(0.01)
		GLITC.atten(channel,atten_dac)
		sleep(5)
	
	time = np.linspace(0,time_step*num_samples,num_samples)
	sample = GLITC.RITC_storage_read(channel,num_reads=num_reads*2)
	sleep(0.01)
	

	plt.figure(figsize=[16,12])
	#plt.plot(time[0:4*32-1],sample[0:4*32-1],label=('Digitized Output: %d MHz Sine Wave (%d mV P2P)'%(input_freq/1000000,input_amp_p2p)))
	plt.plot(time*10**9,sample,linestyle=':',label=('Digitized Output'))
	
	corrected_sample = sample
	
	for i in range(0,len(sample)-1):
		if(sample[i]==7 and sample[i+1]<=4):
			#print "Correcting down"
			corrected_sample[i] = 4

	#plt.plot(time[0:4*32-1],corrected_sample[0:4*32-1],label=('Glitc corrected Digitized Output: %d MHz Sine Wave (%d mV P2P)'%(input_freq/1000000,input_amp_p2p)))
	plt.plot(time*10**9,corrected_sample,label=('Glitch Corrected Digitized Output'))
	#print sample
	#print corrected_sample
	
	#fitfunc = lambda p, x: p[0]*np.sin(2*np.pi*p[1]*x+p[2]) + p[3]
	#errfunc = lambda p, x, y: fitfunc(p,x) - y
	#p0 = [7.0,frequency[max_frequency_bin],0.0,3.5]
	#p1,success = leastsq(errfunc, p0[:], args=(time,sample))
	
	
	
	#plt.plot(time[0:4*32-1],fitfunc(p1,time)[0:4*32-1],label=('Fit: %d MHz Sine Wave (%d mV P2P)'%(p1[1]/1000000,2*abs(p1[0]*54.0))))
	plt.title("%d mV Peak-Peak Impulse - GLITC %d, Ch %d, Ped %d (%d mV), Atten %d (-%1.2f dB)" % (input_amp_p2p,GLITC_n,channel,ped_dac,ped_dac*2500/4095,atten_dac,atten_dac*0.25))
	plt.xlabel("Time [ns]")
	plt.ylabel("Ouput Value")
	plt.legend()
	#plt.grid(True)
	plt.ylim((0,7))
	plt.savefig(("/home/user/data/TISC%d/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_atten_%1.2fdB.png" % (TISC,GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	plt.show()
	plt.close()
	
	corrected_sample_average = np.average(corrected_sample)
	print corrected_sample_average
	
	sample_fft = fft(corrected_sample-corrected_sample_average)
	sample_fft/=num_samples/2
	frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
	max_frequency_bin = np.argmax(2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	print frequency[max_frequency_bin]
	
	plt.figure(figsize=[16,12])
	#plt.axvline(x=input_freq,linestyle="--",color='r',label=("Input Frequency: %dMHz"%(input_freq/1000000)))
	plt.plot(frequency,2.0/num_samples*np.abs(sample_fft[0:num_samples/2]))
	#plt.ylim((0,2.5))
	plt.title("%d mV Peak-Peak Impulse FFT"%(input_amp_p2p))
	#plt.title("Impulse Test")
	plt.xlabel("Frequency [Hz]")
	plt.ylabel("Amplitude")
	plt.legend()
	plt.grid(True)
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (TISC,GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	plt.show()
	#plt.clf()
	#plt.close()
	del corrected_sample
	del sample
	
	return None

# Performs a scan of the pedestal inputs and saves each samples output seperately	
def pedestal_vs_sample_scan(GLITC,GLITC_n,channel,ped_min=525,ped_max=925,ped_step=1,num_reads=255):
	
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads

	#reload(tsd)
	print "Setting channel %d thresholds" % channel
	set_thresholds(GLITC,GLITC_n,channel)
	
	ped_array = np.arange(ped_min,ped_max+1,ped_step)
	num_peds = len(ped_array)
	
	sample_array = np.zeros((samples_per_vcdl,num_peds))
	average_sample = np.zeros(num_peds)
	
	for ped_i in range(num_peds):
		
		print "Setting pedestal to %d"%ped_array[ped_i]
		GLITC.dac(channel,int(ped_array[ped_i]))
		sleep(5)
		
		sample = GLITC.RITC_storage_read(channel,num_reads=num_reads*2)

		#print len(sample)
		for block_i in range(num_reads):
			
			for sample_i in range(samples_per_vcdl):
				sample_array[sample_i,ped_i]+=sample[block_i*samples_per_vcdl+sample_i]
				average_sample[ped_i]+=sample[block_i*samples_per_vcdl+sample_i]
	
	sample_array/=num_reads
	average_sample/=(num_reads*samples_per_vcdl)
	
	"""
	plt.figure(figsize=(16,12))
	for samp_i in range(samples_per_vcdl):
		plt.plot(ped_array,average_sample,label="All sample average")
		plt.plot(ped_array,sample_array[samp_i],label=("Sample %d"%samp_i))
		plt.ylim((0,7))
		plt.legend()
		plt.title("GLITC %d, Ch %d, Sample %d"%(GLITC_n,channel,samp_i))
		plt.xlabel("Pedestal DAC")
		plt.ylabel("Averaged Output")
		plt.savefig(("/home/user/data/TISC%d/GLITC_%d/G%d_Ch%d_sample%d_ped_only.png" % (TISC,GLITC_n,GLITC_n,channel,samp_i)))
		plt.clf()
	plt.show()
	"""
	datafile_array = [0]*2
	
	with open('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only.dat'%(TISC,GLITC_n,channel,GLITC_n,channel),'wb') as f:
		writer = csv.writer(f)
		writer.writerow(['Ped_DAC','Avg_Sample','Samples_0_to_31'])
		for i in range(num_peds):
			datafile_array[0] = ped_array[i]
			datafile_array[1] = average_sample[i]
			writer.writerow(np.concatenate((datafile_array,sample_array[:,i])))
	
	
	return None
	
#Generate data of ped scans for all glitcs and samples... 
#this is actually idential to run_individual_sample_correction_study()
def pedestal_vs_sample_scan_all(ped_min=525,ped_max=925,ped_step=1,num_reads=255):
	
	for GLITC_i in range(2):
		GLITC = setup(GLITC_i)
		for channel_i in range(7):
			if channel_i == 3:
				continue
			#if GLITC_i == 0 and channel_i == 0:
			#	continue
			set_thresholds(GLITC,GLITC_i,channel_i)
			#take the data
			pedestal_vs_sample_scan(GLITC,GLITC_i,channel_i,ped_min=525,ped_max=925,ped_step=1,num_reads=255)
	
	
	return None
			
	
# Take the saved data from the module above and generate plots	
def pedestal_vs_sample_scan_from_file(GLITC_n,channel):
	
	samples_per_vcdl = 32
	ped_array = []
	sample_array = []
	average_sample = []
	offset_min = -2
	offset_max = 2
	offset_step = 0.1
	
	with open('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only.dat'%(TISC,GLITC_n,GLITC_n,channel,channel),'rb') as datafile:
		datareader = csv.reader(datafile, delimiter=',', quotechar='|')
		
		row_number = 0
		header_flag = 0

		# Read in and plot the data
		for row in datareader:
			
			if (header_flag == 0):
				header_flag = 1
			else:			
				ped_array.append(float(row[0]))
				average_sample.append(float(row[1]))
				sample_array.append(row[2:])

	num_peds = len(ped_array)
	ped_array = np.array(ped_array)
	sample_array = np.array(sample_array)
	sample_array = sample_array.astype(np.float)
	sample_array = np.transpose(sample_array)
	
	ideal_coeff = np.polyfit(ped_array,average_sample,1)
	ideal_line = np.zeros(num_peds)
	ideal_line = ideal_coeff[0]*ped_array+ideal_coeff[1]
	rmse_bc = 1/np.sqrt(12)

	gs = gridspec.GridSpec(3,1)
	for samp_i in range(samples_per_vcdl):
		
		rms_error = get_RMS_error(sample_array[samp_i],ideal_line)
		residuals = np.subtract(sample_array[samp_i],ideal_line)
		rms_error = np.sqrt(rmse_bc**2-rms_error**2)
		"""
		fig = plt.figure(figsize=(16,12))
		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.1)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array,sample_array[samp_i],label=("Sample %d (RMSE %1.2f)"%(samp_i,rms_error)),color='b')
		ax1.plot(ped_array,ideal_line,linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0)
		ax1.set_title("GLITC %d, Ch %d, Sample %d"%(GLITC_n,channel,samp_i))
		ax1.set_ylabel("Averaged Output")
		
		
		ax2.plot(ped_array,residuals,label=("Sample - Ideal"))
		ax2.axhline(y=0,linestyle="--",color='r')
		ax2.set_xlabel("Pedestal DAC")
		ax2.legend(loc=3)
		plt.show()
		#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sample_study/channel _%d/G%d_Ch%d_sample%d_ped_only.png" % (TISC,GLITC_n,channel,GLITC_n,channel,samp_i)))
		#plt.clf()
		"""
		best_rms_error,best_offset,rms_corrected_sample_array = minimize_RMS_error(sample_array[samp_i],ideal_line,offset_min,offset_max,offset_step)
		rms_corrected_residuals = np.subtract(rms_corrected_sample_array,ideal_line)
		rms_corrected_residuals = np.sqrt(rmse_bc**2-rms_corrected_residuals**2)
		
		fig = plt.figure(figsize=(8,4))
		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.1)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array,rms_corrected_sample_array,label=("Corrected Sample %d (RMSE %1.2f)"%(samp_i,best_rms_error)),color='b')
		#ax1.plot(ped_array,mean_corrected_sample_array,label=("Sample %d Mean"%samp_i))
		ax1.plot(ped_array,sample_array[samp_i],linestyle=":",color='b',label=("Non-corrected (RMSE %1.2f)"%rms_error))
		ax1.plot(ped_array,ideal_line,linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0,prop={'size':10})
		ax1.set_title("GLITC %d, Ch %d, Sample %d - RMS Corrected by %1.2f"%(GLITC_n,channel,samp_i,best_offset))
		ax1.set_ylabel("Averaged Output")
		
		#residuals = np.subtract(sample_array[samp_i],ideal_line)
		ax2.plot(ped_array,rms_corrected_residuals,label="Corrected Sample - Ideal")
		ax2.plot(ped_array,residuals,linestyle=":",color='b',label="Non-corrected")
		ax2.axhline(y=0,linestyle="--",color='r')
		ax2.set_xlabel("Pedestal DAC")
		ax2.legend(loc=3,prop={'size':10})
		#plt.show()
		plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample%d_ped_only_rmse_corrected.png" % (TISC,GLITC_n,channel,GLITC_n,channel,samp_i)))
		plt.clf()
		plt.close()

	return None

# Take in two array of equal length and find the overall offset that minimizes the RMS error		
def minimize_RMS_error(data,prediction,offset_min,offset_max,offset_step):
	
	best_rms_error = 100000000000000
	offset_array = np.arange(offset_min,offset_max,offset_step)
	for offset_i in range(len(offset_array)):
		
		rms_error = get_RMS_error(data+offset_array[offset_i],prediction)
		
		if(rms_error<best_rms_error):
			best_rms_error = rms_error
			best_offset = offset_array[offset_i]
			
	return best_rms_error,best_offset,data+best_offset

# Take in two arrays of equal length and returns the RMS error		
def get_RMS_error(data,prediction):
	rms_error = np.sqrt(np.mean(np.square(np.subtract(data,prediction))))
	return rms_error

def pedestal_vs_sample_scan_individual_correction_all():
	
	for GLITC_i in range(2):

		for channel_i in range(7):
			if channel_i == 3:
				continue
			if GLITC_i == 0 and channel_i == 0:
				continue
			#take the data from the files, and make plots.
			pedestal_vs_sample_scan_individual_correction(GLITC_i,channel_i)
	
	
	return None


# Takes the saved data from the pedestal sample scan and find the individual sample offsets
def pedestal_vs_sample_scan_individual_correction(GLITC_n,channel):
	
	samples_per_vcdl = 32
	ped_array = []
	sample_array = []
	average_sample = []
	rmse_bc = 1/np.sqrt(12)
	
	offset_min = -2
	offset_max = 2
	offset_step = 0.1
	
	
	
	with open('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only.dat'%(TISC,GLITC_n,channel,GLITC_n,channel),'rb') as datafile:
		datareader = csv.reader(datafile, delimiter=',', quotechar='|')
		
		row_number = 0
		header_flag = 0

		# Read in and plot the data
		for row in datareader:
			
			if (header_flag == 0):
				header_flag = 1
			else:			
				ped_array.append(float(row[0]))
				average_sample.append(float(row[1]))
				sample_array.append(row[2:])
				
	print "Done reading from file"
	num_peds = len(ped_array)
	ped_array = np.array(ped_array)
	sample_array = np.array(sample_array)
	sample_array = sample_array.astype(np.float)
	sample_array = np.transpose(sample_array)
	
	sample_corrected_array = np.zeros((32,len(ped_array)))
	sample_correction = np.zeros((32,len(ped_array)))
	
	ideal_coeff = np.polyfit(ped_array,average_sample,1)
	ideal_line = np.zeros(num_peds)
	ideal_line = ideal_coeff[0]*ped_array+ideal_coeff[1]
	
	hist = [[0 for x in range(8)] for x in range(32)]
	weight = [[0 for x in range(8)] for x in range(32)]
	offsets = [[0 for x in range(8)] for x in range(32)]
	
	rmse_low_bound = int((-0.5-ideal_coeff[1])/ideal_coeff[0])
	rmse_high_bound = int((7.5-ideal_coeff[1])/ideal_coeff[0])
	
	rmse_low_bound_index = (np.abs(ped_array - rmse_low_bound)).argmin()
	rmse_high_bound_index = (np.abs(ped_array - rmse_high_bound)).argmin()
	
	pp = PdfPages("/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_threshold_histograms.pdf" % (TISC,GLITC_n,channel,GLITC_n,channel))
	
	# Find offsets for each sample and each threshold level
	for sample_i in range(32):
		print "Scanning sample %d"%sample_i
		for thres_i in range(8):
			temp_hist = []
			temp_weight = []
			for ped_i in range(num_peds):
				output_val = sample_array[sample_i][ped_i]
				if((thres_i ==7) and (output_val > (6)) and (ped_i < ((7.5-ideal_coeff[1])/ideal_coeff[0]) )):
					temp_hist.append(ped_array[ped_i])
					temp_weight.append( output_val-(thres_i-1) )
				elif((thres_i ==0) and (output_val < (1)) and (ped_i > ((-0.5-ideal_coeff[1])/ideal_coeff[0]) )):
					temp_hist.append(ped_array[ped_i])
					temp_weight.append( (thres_i+1)-output_val )
				elif ((output_val > (thres_i-1)) and (output_val < thres_i)):
					temp_hist.append(ped_array[ped_i])
					temp_weight.append( output_val-(thres_i-1) )
				elif (output_val == thres_i ):
					temp_hist.append(ped_array[ped_i])
					temp_weight.append(1)
				elif ((output_val > (thres_i)) and (output_val < (thres_i+1))):
					temp_hist.append(ped_array[ped_i])
					temp_weight.append( (thres_i+1)-output_val )
			if(len(temp_hist)!=0):
				hist[sample_i][thres_i] = temp_hist
				weight[sample_i][thres_i] = temp_weight	
			
				plot_hist,bin_edges = np.histogram(hist[sample_i][thres_i],len(ped_array),weights=weight[sample_i][thres_i],range=[np.amin(ped_array),np.amax(ped_array)])
				mu,sigma = norm.fit(hist[sample_i][thres_i])
				offsets[sample_i][thres_i] = (-1)*round((float(thres_i) - float(ideal_coeff[0]*mu+ideal_coeff[1]))*8)/8.0
			else:
				offsets[sample_i][thres_i] = 0
			
			'''
			#for some reason we make a hist, but just for thres 4? looking for 7 glitches?
			if(thres_i==3):
				plt.figure(figsize=(8,4))
				plt.hist(hist[sample_i][thres_i],len(ped_array)/2,weights=np.array(weight[sample_i][thres_i])/2.0,range=[np.amin(ped_array),np.amax(ped_array)],label=("Mu %1.2f"%mu))
				plt.axvline(mu)
				#plt.xlim(np.amin(hist[sample_i][thres_i]),np.amax(hist[sample_i][thres_i]))
				plt.xlim(np.amin(ped_array),np.amax(ped_array))
				plt.xlabel("Pedestal DAC")
				plt.ylabel("Counts")
				plt.title("GLITC %d, Ch %d, Sample %d, Threshold %d Histogram"%(GLITC_n,channel,sample_i,thres_i))
				plt.axis([500,950,0,1.1])
				#plt.savefig(pp, format='pdf')
				plt.show()
				plt.clf()
			'''
			
			sample_correction[sample_i] = np.add(plot_hist*offsets[sample_i][thres_i],sample_correction[sample_i])

	
		
		sample_corrected_array[sample_i] = np.add(sample_correction[sample_i],sample_array[sample_i])
		
	#pp.close()
	"""
	plt.figure(figsize=(16,12))	
	plt.hist(np.reshape(offsets,32*8),16)
	plt.title("GLITC %d, Ch %d Sample Offset Histogram"%(GLITC_n,channel))
	plt.xlabel("Offsets [threshold levels]")
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_all_offsets_histogram.png" % (TISC,GLITC_n,channel,GLITC_n,channel)))
	#plt.show()
	plt.clf()
	plt.close()
	"""
	
	# Save sample_threshold offsets
	with open('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(TISC,GLITC_n,channel,GLITC_n,channel),'wb') as f:
		writer = csv.writer(f)
		for i in range(samples_per_vcdl):
			writer.writerow(offsets[i])
	
	# Make plots
	gs = gridspec.GridSpec(3,1)
	for samp_i in range(samples_per_vcdl):
		
		rms_error = get_RMS_error(sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		residuals = np.subtract(sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		rms_error = np.sqrt(abs(rmse_bc**2-rms_error**2))
		
		"""
		fig = plt.figure(figsize=(16,12))
		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.1)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array,sample_array[samp_i],label=("Sample %d (RMSE %1.2f)"%(samp_i,rms_error)),color='b')
		ax1.plot(ped_array,ideal_line,linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0)
		ax1.set_title("GLITC %d, Ch %d, Sample %d"%(GLITC_n,channel,samp_i))
		ax1.set_ylabel("Averaged Output")
		
		
		ax2.plot(ped_array,residuals,label=("Sample - Ideal"))
		ax2.axhline(y=0,linestyle="--",color='r')
		ax2.set_xlabel("Pedestal DAC")
		ax2.legend(loc=3)
		plt.show()
		#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sample_study/channel _%d/G%d_Ch%d_sample%d_ped_only.png" % (TISC,GLITC_n,channel,GLITC_n,channel,samp_i)))
		#plt.clf()
		"""
		best_rms_error,best_offset,rms_corrected_sample_array = minimize_RMS_error(sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index],offset_min,offset_max,offset_step)
		rms_corrected_residuals = np.subtract(rms_corrected_sample_array,ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		#rms_corrected_residuals = np.sqrt(abs(rmse_bc**2-rms_corrected_residuals**2))
		best_rms_error = np.sqrt(abs(rmse_bc**2-best_rms_error**2))
		
		ind_corr_rms_error = get_RMS_error(sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		ind_corr_residuals = np.subtract(sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		ind_corr_rms_error = np.sqrt(abs(rmse_bc**2-ind_corr_rms_error**2))
		
		fig = plt.figure(figsize=(8,4))

		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.3)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],linestyle=":",color='b',label=("Non-corrected (RMSE %1.2f)"%rms_error))
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],rms_corrected_sample_array,label=("Mean Corrected Sample %d (RMSE %1.2f)"%(samp_i,best_rms_error)),color='b')
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],label=("INL Corrected Sample %d (RMSE %1.2f)"%(samp_i,ind_corr_rms_error)),color='g')
		#plt.xlim(ped_array[rmse_low_bound_index],ped_array[rmse_high_bound_index])
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index],linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0,prop={'size':10})
		ax1.set_title("GLITC %d, Ch %d, Sample %d Corrected Transfer Curves"%(GLITC_n,channel,samp_i))
		#ax1.set_title("GLITC %d, Ch %d, Sample %d Transfer Curve"%(GLITC_n,channel,samp_i))
		ax1.set_ylabel("Averaged Output")
		
		#residuals = np.subtract(sample_array[samp_i],ideal_line)
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],residuals,linestyle=":",color='b',label="Non-corrected")
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],rms_corrected_residuals,label="Mean Corrected")
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],ind_corr_residuals,linestyle="-",color='g',label="INL Corrected")
		ax2.axhline(y=0.0,linestyle="--",color='r')
		
		ax2.set_xlabel("Pedestal DAC")
		#ax2.legend(loc=3,prop={'size':10})
		#plt.xlim(ped_array[rmse_low_bound_index],ped_array[rmse_high_bound_index])
		
		plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample%d_ped_only_ind_thres_corrected.png" % (TISC,GLITC_n,channel,GLITC_n,channel,samp_i)))
		#if(samp_i==3):
		#	plt.show()
		plt.clf()
		plt.close()

	return None

# Function to make the folder structure to store data
def make_folder_structure(TISC_n=TISC):
	mypath = '../data/TISC%d'%TISC_n
	if not os.path.exists(mypath):
		os.makedirs(mypath)
		
	for GLITC_i in range(4):
		mypath = '../data/TISC%d/GLITC_%d'%(TISC_n,GLITC_i)
		if not os.path.exists(mypath):
			os.makedirs(mypath)
		mypath = '../data/TISC%d/GLITC_%d/threshold_study'%(TISC_n,GLITC_i)
		if not os.path.exists(mypath):
			os.makedirs(mypath)			
		mypath = '../data/TISC%d/GLITC_%d/transition_study'%(TISC_n,GLITC_i)
		if not os.path.exists(mypath):
			os.makedirs(mypath)			
		mypath = '../data/TISC%d/GLITC_%d/sample_study'%(TISC_n,GLITC_i)
		if not os.path.exists(mypath):
			os.makedirs(mypath)	
		for channel_i in range(7):
			if channel_i == 3:
				continue
			mypath = '../data/TISC%d/GLITC_%d/sample_study/channel_%d'%(TISC_n,GLITC_i,channel_i)
			if not os.path.exists(mypath):
				os.makedirs(mypath)
		for RITC_i in range(2):
			mypath = '../data/TISC%d/GLITC_%d/RITC_%d'%(TISC_n,GLITC_i,RITC_i)
			if not os.path.exists(mypath):
				os.makedirs(mypath)
			for Channel_i in range(3):
				mypath = '../data/TISC%d/GLITC_%d/RITC_%d/Ch_%d'%(TISC_n,GLITC_i,RITC_i,Channel_i)
				if not os.path.exists(mypath):
					os.makedirs(mypath)
	
	
	return None


def make_threshold_offset_dictionary(TISC_n=TISC):
	#need to write this still....
	dict = open('/home/user/data/TISC%d/TISC_threshold_offset_dictionary.py'%(TISC_n), 'w')
	dict.write('def get_offsets(TISC_n,GLITC_n,channel,RITC_COMP):\n')
	dict.write('	offset_dict = {}\n\n')
	dict.write('	# Syntax (TISC_Number,GLITC_Number,Channel_Number,RITC_DAC_Number,Transition_Point) = offset \n\n\n')

	for GLITC_i in range(2):
		
		dict.write('	#------------------------------------------------------- \n')
		dict.write('	#----------------------GLITC %d-------------------------- \n'%(GLITC_i))
		dict.write('	#------------------------------------------------------- \n\n')
		
		for channel_i in range(7):
			
			if channel_i == 3:
				continue
			
			dict.write('	#TISC %d \n'%(TISC_n))
			dict.write('	#GLITC %d \n'%(GLITC_i))
			dict.write('	#Channel %d \n\n'%(channel_i))

			RITC_COMP = []
			transition_location = []
			offset_settings = []
			rms_error = []
			header_flag = 0
			with open('/home/user/data/TISC%d/GLITC_%d/transition_study/GLITC_%d_channel_%d_transition_offsets_1.dat'%(TISC_n,GLITC_i,GLITC_i,channel_i),'rb') as datafile:
				datareader = csv.reader(datafile, delimiter=',', quotechar='|')
				for row in datareader:
					if (header_flag == 0):
						header_flag=1
					else:
						RITC_COMP.append(float(row[2]))
						transition_location.append(float(row[4]))
						offset_settings.append(float(row[7]))
						rms_error.append(float(row[10]))
			datafile.close
			for i in range(len(offset_settings)):
				if (transition_location[i] == 1536):
					dict.write('	offset_dict[(%d,%d,%d,%d,512)] = %d'%(TISC_n,GLITC_i,channel_i,RITC_COMP[i],int(offset_settings[i])))
					if (abs(rms_error[i]) >= 1.75):
						dict.write(' #rms_error = %d, further investigation recommended \n'%rms_error[i])
					else:
						dict.write('\n')
				elif (transition_location[i] == 1280 or transition_location[i] == 1792):
					dict.write('	offset_dict[(%d,%d,%d,%d,256)] = %d'%(TISC_n,GLITC_i,channel_i,RITC_COMP[i],int(offset_settings[i])))
					if (abs(rms_error[i]) >= 1.75):
						dict.write(' #rms_error = %d, further investigation recommended \n'%rms_error[i])
					else:
						dict.write('\n')
					dict.write('	offset_dict[(%d,%d,%d,%d,128)] = 0 \n\n'%(TISC_n,GLITC_i,channel_i,RITC_COMP[i]))
				elif (transition_location[i] == 1152 or transition_location[i] == 1408 or transition_location[i] == 1664 or transition_location[i] == 1920):
					transition_location[i] = 128
					#If there are actually 128 transitions mesured then this part will need to be modified.
				else:
					dict.write('	offset_dict[(%d,%d,%d,%d,%d)] = %d \n'%(TISC_n,GLITC_i,channel_i,RITC_COMP[i],transition_location[i],int(offset_settings[i])))
			dict.write('\n')
			del RITC_COMP
			del transition_location
			del offset_settings
			del rms_error
		dict.write('\n')
	dict.write('	return offset_dict[(TISC_n,GLITC_n,channel,RITC_COMP,2048)],offset_dict[(TISC_n,GLITC_n,channel,RITC_COMP,1024)],offset_dict[(TISC_n,GLITC_n,channel,RITC_COMP,512)],offset_dict[(TISC_n,GLITC_n,channel,RITC_COMP,256)],offset_dict[(TISC_n,GLITC_n,channel,RITC_COMP,128)]')
	dict.close
	
	return None	

def make_threshold_setting_dictionary(TISC_n=TISC):
	
	dict = open('/home/user/data/TISC%d/TISC_threshold_setting_dictionary.py'%(TISC_n), 'w')	
	dict.write('def get_threshold(TISC_n,GLITC_n,channel,RITC_COMP):\n')
	dict.write('	thresh_dict = {}\n\n')
	dict.write('	# Syntax (TISC_Number,GLITC_Number,Channel_Number,RITC_DAC_Number) = transition_setting \n\n\n')

	for GLITC_i in range(2):
		
		dict.write('	#------------------------------------------------------- \n')
		dict.write('	#----------------------GLITC %d-------------------------- \n'%(GLITC_i))
		dict.write('	#------------------------------------------------------- \n\n')
		
		for channel_i in range(7):
			
			if channel_i == 3:
				continue
			
			dict.write('	#TISC %d \n'%(TISC_n))
			dict.write('	#GLITC %d \n'%(GLITC_i))
			dict.write('	#Channel %d \n'%(channel_i))

			thresh_settings = []
			header_flag = 0
			with open('/home/user/data/TISC%d/GLITC_%d/threshold_study/G%d_Ch%d_settings_3.dat'%(TISC_n,GLITC_i,GLITC_i,channel_i),'rb') as datafile:
				datareader = csv.reader(datafile, delimiter=',', quotechar='|')
				for row in datareader:
					if (header_flag < 7):
						header_flag+=1
					else:
						for thresh_i in range(7):
							thresh_settings.append(float(row[thresh_i]))
			datafile.close
			for thresh_label_i in range(1,8):
				RITC, RITC_COMP = get_channel_info(channel_i,thresh_label_i)
				dict.write('	thresh_dict[(%d,%d,%d,%d)] = %d \n'%(TISC_n,GLITC_i,channel_i,RITC_COMP,int(thresh_settings[thresh_label_i-1])))
			dict.write('\n')
			del thresh_settings
		dict.write('\n')
	dict.write('	return thresh_dict[(TISC_n,GLITC_n,channel,RITC_COMP)]')
	dict.close
	
	return None	

# Read the individual sample offsets file and returns a 2d matrix [sample]x[threshold_level]
def get_individual_sample_offsets(GLITC_n,channel):
	
	offsets = [[0 for x in range(8)] for x in range(32)]
	row_counter = 0
	with open('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(TISC,GLITC_n,channel,GLITC_n,channel),'rb') as datafile:
		datareader = csv.reader(datafile, delimiter=',', quotechar='|')
		# Read in and plot the data
		for row in datareader:
			for thres_i in range(8):
				offsets[row_counter][thres_i] = float(row[thres_i])			
			row_counter+=1
	
	
	return offsets
	
#makes the INL correction dictionary from the INL correction files in a numaric offset form	
def make_INL_correction_dictionary_file(TISC_n=TISC):
	
	dict = open('/home/user/data/TISC%d/TISC_INL_correction_dictionary.py'%(TISC_n), 'w')	
	dict.write('def get_INL_correction(TISC_n,GLITC_n,channel,sample):\n')
	dict.write('	INL_correction_dict = {}\n\n')
	dict.write('	#INL_Correction_dict[(TISC,GLITC,Channel,Sample)]={Thres 1, Thres 2, ect} \n\n\n')
	
	for GLITC_i in range(4):
		
		dict.write('	#------------------------------------------------------- \n')
		dict.write('	#----------------------GLITC %d-------------------------- \n'%(GLITC_i))
		dict.write('	#------------------------------------------------------- \n\n')
		
		for channel_i in range(7):
			
			if channel_i == 3:
				continue
			
			dict.write('	#TISC %d \n'%(TISC_n))
			dict.write('	#GLITC %d \n'%(GLITC_i))
			dict.write('	#Channel %d \n\n'%(channel_i))
			
			Offsets = [[0 for x in range(8)] for x in range(32)]
			if os.path.isfile('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(TISC_n,GLITC_i,channel_i,GLITC_i,channel_i)):
				Offsets = get_individual_sample_offsets(GLITC_i,channel_i)
			
			for Sample_i in range(32):
				dict.write('	INL_correction_dict[(%d,%d,%d,%2d)] = (% .3f, % .3f, % .3f, % .3f, % .3f, % .3f, % .3f) \n'%(TISC_n,GLITC_i,channel_i,Sample_i,Offsets[Sample_i][0],Offsets[Sample_i][1],Offsets[Sample_i][2],Offsets[Sample_i][3],Offsets[Sample_i][4],Offsets[Sample_i][5],Offsets[Sample_i][6]))
			
			dict.write('\n\n')
	
	dict.write('	return INL_correction_dict[(TISC_n,GLITC_n,channel,sample)]')
	dict.close
	
	return None	

#returns INL correction for one sample as 42 bit string.

def get_binary_INL_correction(TISC_n,GLITC_n,channel,sample):
	#INL_correction_array = np.zeros(7)
	INL_array = INLd.get_INL_correction(TISC_n,GLITC_n,channel,sample)
	corrected_array= []
	binary_string = ''
	for thres_i in range(7):
		temp_value = INL_array[thres_i]+(thres_i+1)
		corrected_array.append( '{0:06b}'.format(int(8*temp_value)) )
	
	#rotate matrix so first bit of all 7 thresholds are listed, then second bit, ect...
	for bit_i in range(5):
		for thres_j in range(7):
			binary_string= binary_string+corrected_array[thres_j][bit_i]
	return binary_string
	

def make_INL_bin_correction_dictionary_file(TISC_n):
	
	dict = open('/home/user/data/TISC%d/TISC_Bin_INL_correction_dictionary.py'%(TISC_n), 'w')
	dict.write('def get_binary_INL_correction(TISC_n, GLITC_n, channel, sample):\n')
	dict.write('    binary_INL_correction_dict = {}\n\n')
	dict.write('    #binary_INL_correction_dict[(TISC,GLITC,Channel,Sample)]={Binary_INL 1, Binary_INL 2, ect} \n\n\n')

	
	for GLITC_i in range(4):
		
		dict.write('    #------------------------------------------------------ \n')
		dict.write('    #----------------------GLITC %d------------------------- \n'%(GLITC_i))
		dict.write('    #------------------------------------------------------ \n\n')
        
		for channel_i in range(7):
			
			if channel_i == 3:
				continue
			
			dict.write('    #TISC %d \n'%(TISC_n))
			dict.write('    #GLITC %d \n'%(GLITC_i)) 
			dict.write('	#Channel %d \n\n'%(channel_i))
			
			 
			if os.path.isfile('/home/user/data/TISC%d/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(TISC_n,GLITC_i,channel_i,GLITC_i,channel_i)):
				Offsets = get_individual_sample_offsets(GLITC_i,channel_i)
				
			for Sample_i in range(32):
				Binary = get_binary_INL_correction(TISC_n, GLITC_i, channel_i, Sample_i)
				dict.write('    binary_INL_correction_dict[(%d,%d,%d,%2d)] =  %s \n'%(TISC_n, GLITC_i, channel_i, Sample_i, Binary))
			
			dict.write('\n\n')
			
	dict.write('    return binary_INL_correction_dict[(TISC_n,GLITC_n,channel,sample)]')	 	
	dict.close
    
	return None
    
# Take in a sample array and a offsets matrix and corrects it
def correct_individual_samples(sample_array,offsets):
	
	if(len(sample_array)%32!=0):
		print "Samples array must include all 32 samples and begin with sample 0!"
		return 1
	
	num_sample_blocks = int(len(sample_array)/32)
	
	return_array = np.zeros(len(sample_array))
	
	for block_i in range(num_sample_blocks):
		for samp_i in range(32):
			threshold_level = int(sample_array[32*block_i+samp_i])
			#print threshold_level
			return_array[32*block_i+samp_i] = sample_array[32*block_i+samp_i] + offsets[samp_i][threshold_level]
	
	return return_array


def round_to_nearest_half(sample_array):
	
	rounded_array = [0]*len(sample_array)
	
	
	for i in range(len(sample_array)):
		
		sign = np.sign(sample_array[i])
		#print "sign:%d"%sign
		sample_decimal = int((abs(sample_array[i])-int(abs(sample_array[i])))*8.0)
		#print "sample_decimal:%d"%sample_decimal
		
		if(sample_decimal == 7 or sample_decimal == 3 or sample_decimal ==6):
			rounded_array[i] = math.floor(abs(sample_array[i])*2+1)/2
		else:
			rounded_array[i] = math.floor(abs(sample_array[i])*2)/2
		
		rounded_array[i]*=sign
		
	return rounded_array

# Do all the operations that the GLITC will to and return the correlated sum
def perform_GLITC_ops(A,B,C):


	# Add samples together
	abc_add = np.add(np.add(A,B),C)
	#print abc_add
	
	# Round to nearest 0.5
	abc_add_rounded = round_to_nearest_half(abc_add)
	#print abc_add_rounded
	
	# Square
	abc_square = np.square(abc_add_rounded)
	#print abc_square
	
	# Sum
	correlated_sum = np.sum(abc_square)
	

	return correlated_sum, abc_add, abc_add_rounded, abc_square


def RITC_storage_3ch(GLITC,GLITC_n,RITC,ped_dac=730,atten_dac=16,num_reads=1):
	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	datetime = strftime("%Y_%M_%d_%H:%m:%S")
	
	reload(tsd)
	reload(tisc)
	for ch_i in range(RITC*4,RITC*4+3):
		print "Setting channel %d thresholds" % ch_i
		set_thresholds(GLITC,GLITC_n,ch_i)
	
		if(GLITC.dac(ch_i)!=ped_dac):
			sleep(0.01)
			GLITC.dac(ch_i,ped_dac)
			sleep(5)
			
		if(GLITC.atten(ch_i)!=atten_dac):
			sleep(0.01)
			GLITC.atten(ch_i,atten_dac)
			sleep(5)
		
	a_offsets = get_individual_sample_offsets(GLITC_n,RITC*4)
	b_offsets = get_individual_sample_offsets(GLITC_n,RITC*4+1)
	c_offsets = get_individual_sample_offsets(GLITC_n,RITC*4+2)
		
	time = np.linspace(0,time_step*num_samples,num_samples)*10**9
	a_sample,b_sample,c_sample = GLITC.RITC_storage_read_3ch(RITC,num_reads=num_reads*2)
	sleep(0.01)

	a_corrected_sample = do_glitch_correction(a_sample)
	b_corrected_sample = do_glitch_correction(b_sample)
	c_corrected_sample = do_glitch_correction(c_sample)

	# Individual Sample Correction
	a_corrected_sample = np.array(correct_individual_samples(a_corrected_sample,a_offsets))-3.5
	b_corrected_sample = np.array(correct_individual_samples(b_corrected_sample,b_offsets))-3.5
	c_corrected_sample = np.array(correct_individual_samples(c_corrected_sample,c_offsets))-3.5
	
	a_sample = np.array(a_sample)-3.5
	b_sample = np.array(b_sample)-3.5
	c_sample = np.array(c_sample)-3.5
	
	############################################
	# Build up matrix to write to file
	write_matrix = [[0 for x in range(7)] for x in range(num_samples)]
	file_loc = "/home/user/data/TISC%d/GLITC_%d/impulse_only_study/Event_data"%(TISC,GLITC_n)
	filename = datetime+"_impulse_only.dat"
	
	for i in range(num_samples):
		write_matrix[i][0] = time[i]
		write_matrix[i][1] = a_sample[i]
		write_matrix[i][2] = b_sample[i]
		write_matrix[i][3] = c_sample[i]
		write_matrix[i][4] = a_corrected_sample[i]
		write_matrix[i][5] = b_corrected_sample[i]
		write_matrix[i][6] = c_corrected_sample[i]
		
	write_to_file(file_loc,filename,write_matrix)
	###############################################
	
	
	
	# For plotting pure digitization noise
	plt.figure(1,figsize=(8,4))
	#plt.plot(available_time_window,available_window)
	plt.plot(time[0:160],a_sample[0:160],label='Ch A',color='k')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(a_sample))))))
	plt.plot(time[0:160],b_sample[0:160],label='Ch B',color='r')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(b_sample))))))
	plt.plot(time[0:160],c_sample[0:160],label='Ch C',color='b')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(c_sample))))))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC %d, Digitization Noise (Uncorrected)")%(GLITC_n,RITC))
	plt.xlabel("Time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	plt.legend(prop={'size':10})
	#plt.show()
	#plt.clf()
	#plt.close()
	
	plt.figure(2,figsize=(8,4))
	#plt.plot(available_time_window,available_window)
	plt.plot(time[0:160],a_corrected_sample[0:160],label='Ch A',color='k')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(a_corrected_sample))))))
	plt.plot(time[0:160],b_corrected_sample[0:160],label='Ch B',color='r')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(b_corrected_sample))))))
	plt.plot(time[0:160],c_corrected_sample[0:160],label='Ch C',color='b')#("RMS: %1.2f"%(np.sqrt(np.mean(np.square(c_corrected_sample))))))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC %d, Digitization Noise")%(GLITC_n,RITC))
	plt.xlabel("Time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	plt.legend(prop={'size':10})
	plt.show()
	plt.clf()
	plt.close()
	
	correlated_sum,abc_add,abc_add_rounded,abc_square = perform_GLITC_ops(a_corrected_sample,b_corrected_sample,c_corrected_sample)
	uncorrected_correlated_sum, uncorrected_abc_add, uncorrected_abc_add_rounded,uncorrected_abc_square = perform_GLITC_ops(a_sample,b_sample,c_sample)
	
	corrected_add_rounded_peak_position, corrected_add_rounded_impulse_ptp, corrected_add_rounded_impulse_sum, corrected_add_rounded_noise_rms, corrected_add_rounded_noise_sum, corrected_add_rounded_SNR, dummy_sum = do_SNR_analysis(abc_add_rounded,time)
	corrected_square_peak_position, corrected_square_impulse_ptp, corrected_square_impulse_sum, corrected_square_noise_rms, corrected_square_noise_sum, corrected_square_SNR, corrected_correlated_sum = do_SNR_analysis(abc_square,time)
	
	uncorrected_add_rounded_peak_position, uncorrected_add_rounded_impulse_ptp, uncorrected_add_rounded_impulse_sum, uncorrected_add_rounded_noise_rms, uncorrected_add_rounded_noise_sum, uncorrected_add_rounded_SNR, dummy_sum = do_SNR_analysis(uncorrected_abc_add_rounded,time)
	uncorrected_square_peak_position, uncorrected_square_impulse_ptp,  uncorrected_square_impulse_sum, uncorrected_square_noise_rms, uncorrected_square_noise_sum, uncorrected_square_SNR, uncorrected_correlated_sum = do_SNR_analysis(uncorrected_abc_square,time)
	
	print "\nCorrected Waveform Information"
	print "Impulse Peak-to-Peak: %1.2f"% corrected_square_impulse_ptp
	print "Peak location in time %1.2fns"% (time[corrected_square_peak_position])
	print "Noise RMS: %1.2f"% corrected_square_noise_rms
	print "SNR: %1.2f"% corrected_square_SNR
	print "Impulse Sum: %1.2f"% corrected_square_impulse_sum
	print "Noise Sum: %1.2f"% corrected_square_noise_sum
	print "Correlated Sum: %1.2f\n"% corrected_correlated_sum

	print "Uncorrected Waveform Information"
	print "Impulse Peak-to-Peak: %1.2f"% uncorrected_square_impulse_ptp
	print "Peak location in time %1.2fns"% (time[uncorrected_square_peak_position])
	print "Noise RMS: %1.2f"% uncorrected_square_noise_rms
	print "SNR: %1.2f"% uncorrected_square_SNR
	print "Impulse Sum: %1.2f"% uncorrected_square_impulse_sum
	print "Noise Sum: %1.2f"% uncorrected_square_noise_sum
	print "Correlated Sum: %1.2f\n"% uncorrected_correlated_sum
	
	"""
	window_width=1000
	#plot_array_y = abc_add_rounded[corrected_square_peak_position-window_width/2:corrected_square_peak_position+window_width/2]
	plot_array_y = abc_square[corrected_add_rounded_peak_position-window_width/2:corrected_add_rounded_peak_position+window_width/2]
	plot_array_x = time[corrected_square_peak_position-window_width/2:corrected_square_peak_position+window_width/2]
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(plot_array_x,plot_array_y,label=("SNR: %1.2f"%corrected_square_SNR))
	plt.ylim([0,110.5])
	plt.title("GLITC %d, RITC %d, Corrected Power w/ 200mV PTP Impulse"%(GLITC_n,RITC))
	plt.xlabel("time [ns]") 
	plt.ylabel("Power [DAC^2]")
	plt.legend()
	plt.show()
	plt.clf()
	plt.close()
	
	plt.figure(figsize=([16,12]))
	plot_array_y = uncorrected_abc_square[uncorrected_square_peak_position-window_width/2:uncorrected_square_peak_position+window_width/2]
	plot_array_x = time[uncorrected_square_peak_position-window_width/2:uncorrected_square_peak_position+window_width/2]
	
	plt.plot(plot_array_x,plot_array_y,label=("SNR: %1.2f"%uncorrected_square_SNR))
	plt.ylim([0,110.5])
	plt.title("GLITC %d, RITC %d, Uncorrected Power w/ 200mV PTP Impulse"%(GLITC_n,RITC))
	plt.xlabel("time [ns]") 
	plt.ylabel("Power [DAC^2]")
	plt.legend()
	plt.show()
	plt.clf()
	plt.close()
	"""
	
	#######################################################
	
	
	# Plot Stuff
	plot_arraya = a_corrected_sample
	plot_arrayb = b_corrected_sample
	plot_arrayc = c_corrected_sample
	print "Correlation Sum: %1.2f"%correlated_sum
	
	plt.figure(figsize=(16,12))
	plt.plot(time,plot_arraya)
	plt.plot(time,plot_arrayb)
	plt.plot(time,plot_arrayc)
	plt.title(("GLITC %d, RITC %d ("+datetime+")")%(GLITC_n,RITC))
	plt.xlabel("Time[ns]")
	plt.ylabel("RITC Output")
	plt.ylim([-3.5,3.5])
	plt.ylim([-10.5,10.5])
	plt.show()
	plt.clf()
	plt.close()
	
	plot_array = abc_add_rounded
	
	plt.figure(figsize=(16,12))
	plt.plot(time,plot_array)
	plt.title(("GLITC %d, RITC %d ABC Added ("+datetime+")")%(GLITC_n,RITC))
	plt.xlabel("Time[ns]")
	plt.ylabel("ABC Added Output")
	plt.ylim([-10.5,10.5])
	plt.ylim([-10.5,10.5])
	plt.show()
	plt.clf()
	plt.close()
	
	plot_array = abc_square
	
	plt.figure(figsize=(16,12))
	plt.plot(time,plot_array,label="SNR: %1.2f"%corrected_square_SNR)
	plt.title(("GLITC %d, RITC %d Squared ("+datetime+")")%(GLITC_n,RITC))
	plt.xlabel("Time[ns]")
	plt.ylabel("ABC Added Output")
	plt.ylim([0,100])
	#plt.ylim([-10.5,10.5])
	plt.legend(loc=0)
	plt.show()
	plt.clf()
	plt.close()
	
	
	"""
	plot_array_average = np.average(plot_array)
	
	sample_fft = fft(plot_array-plot_array_average)
	sample_fft/=num_samples/2
	frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
	max_frequency_bin = np.argmax(2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	print frequency[max_frequency_bin]
	
	plt.figure(figsize=[16,12])
	#plt.axvline(x=input_freq,linestyle="--",color='r',label=("Input Frequency: %dMHz"%(input_freq/1000000)))
	plt.plot(frequency/10**6,2.0/num_samples*np.abs(sample_fft[0:num_samples/2]))
	#plt.ylim((0,2.5))
	plt.title("Squared Board Noise FFT")
	#plt.title("Impulse Test")
	plt.xlabel("Frequency [MHz]")
	plt.ylabel("Amplitude")
	plt.legend()
	plt.grid(True)
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (TISC,GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	#plt.show()
	#plt.clf()
	#plt.close()
	#del corrected_sample
	#del sample
	"""
	return corrected_square_SNR, corrected_square_impulse_sum, corrected_square_noise_sum, corrected_correlated_sum, uncorrected_square_SNR, uncorrected_square_impulse_sum, uncorrected_square_noise_sum, uncorrected_correlated_sum


def sample_correction_comparison(GLITC,GLITC_n,ped_dac=730,atten_dac=2,num_reads=1):
	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	datetime = strftime("%Y_%M_%d_%H:%m:%S")
	
	mean_offset_max = 2
	mean_offset_min = -2
	mean_offset_step = 0.1
	
	reload(tsd)
	reload(tisc)
	atten_array = [2,4,0,2,0,3]
	#atten_array = [0,4,0,2,0,1]
	for ch_i in range(7):
		if(ch_i==3):
			continue
		print "Setting channel %d thresholds" % ch_i
		set_thresholds(GLITC,GLITC_n,ch_i)
	
		if(GLITC.dac(ch_i)!=ped_dac):
			sleep(0.01)
			GLITC.dac(ch_i,ped_dac)
			sleep(5)
	for ch_i in range(6):		
		if(GLITC.atten(ch_i)!=atten_dac+atten_array[ch_i]):
			sleep(0.01)
			print "Setting channel %d attenuation" % ch_i
			GLITC.atten(ch_i,atten_dac+atten_array[ch_i])
			sleep(5)

		
	a_offsets = get_individual_sample_offsets(GLITC_n,0)
	b_offsets = get_individual_sample_offsets(GLITC_n,1)
	c_offsets = get_individual_sample_offsets(GLITC_n,2)
	d_offsets = get_individual_sample_offsets(GLITC_n,4)
	e_offsets = get_individual_sample_offsets(GLITC_n,5)
	f_offsets = get_individual_sample_offsets(GLITC_n,6)
		
	time = np.linspace(0,time_step*num_samples,num_samples)*10**9
	zero_line = np.zeros(num_samples)
	a_sample,b_sample,c_sample,d_sample,e_sample,f_sample = GLITC.RITC_storage_read_6ch(num_reads=num_reads*2)
	sleep(0.01)

	a_corrected_sample = do_glitch_correction(a_sample)
	b_corrected_sample = do_glitch_correction(b_sample)
	c_corrected_sample = do_glitch_correction(c_sample)
	d_corrected_sample = do_glitch_correction(d_sample)
	e_corrected_sample = do_glitch_correction(e_sample)
	f_corrected_sample = do_glitch_correction(f_sample)
	"""
	a_corrected_sample = np.array(a_sample)
	b_corrected_sample = np.array(b_sample)
	c_corrected_sample = np.array(c_sample)
	d_corrected_sample = np.array(d_sample)
	e_corrected_sample = np.array(e_sample)
	f_corrected_sample = np.array(f_sample)
	"""
	#print np.array(minimize_RMS_error(a_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step))

	# Mean Correction
	a_best_RMSE,a_best_offset,a_mean_corrected_sample = minimize_RMS_error(a_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)
	b_best_RMSE,b_best_offset,b_mean_corrected_sample = minimize_RMS_error(b_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)
	c_best_RMSE,c_best_offset,c_mean_corrected_sample = minimize_RMS_error(c_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)
	d_best_RMSE,d_best_offset,d_mean_corrected_sample = minimize_RMS_error(d_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)
	e_best_RMSE,e_best_offset,e_mean_corrected_sample = minimize_RMS_error(e_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)
	f_best_RMSE,f_best_offset,f_mean_corrected_sample = minimize_RMS_error(f_corrected_sample-3.5,zero_line,mean_offset_min,mean_offset_max,mean_offset_step)

	a_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(a_mean_corrected_sample)))
	b_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(b_mean_corrected_sample)))
	c_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(c_mean_corrected_sample)))
	d_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(d_mean_corrected_sample)))
	e_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(e_mean_corrected_sample)))
	f_mean_corrected_sample_rms = np.sqrt(np.mean(np.square(f_mean_corrected_sample)))
	avg_mean_corrected_rms = (a_mean_corrected_sample_rms+b_mean_corrected_sample_rms+c_mean_corrected_sample_rms+d_mean_corrected_sample_rms+e_mean_corrected_sample_rms+f_mean_corrected_sample_rms)/6.0
	
	# INL Correction
	a_corrected_sample = np.array(correct_individual_samples(a_corrected_sample,a_offsets))-3.5
	b_corrected_sample = np.array(correct_individual_samples(b_corrected_sample,b_offsets))-3.5
	c_corrected_sample = np.array(correct_individual_samples(c_corrected_sample,c_offsets))-3.5
	d_corrected_sample = np.array(correct_individual_samples(d_corrected_sample,d_offsets))-3.5
	e_corrected_sample = np.array(correct_individual_samples(e_corrected_sample,e_offsets))-3.5
	f_corrected_sample = np.array(correct_individual_samples(f_corrected_sample,f_offsets))-3.5
	
	a_corrected_sample_rms = np.sqrt(np.mean(np.square(a_corrected_sample)))
	b_corrected_sample_rms = np.sqrt(np.mean(np.square(b_corrected_sample)))
	c_corrected_sample_rms = np.sqrt(np.mean(np.square(c_corrected_sample)))
	d_corrected_sample_rms = np.sqrt(np.mean(np.square(d_corrected_sample)))
	e_corrected_sample_rms = np.sqrt(np.mean(np.square(e_corrected_sample)))
	f_corrected_sample_rms = np.sqrt(np.mean(np.square(f_corrected_sample)))
	avg_corrected_rms = (a_corrected_sample_rms+b_corrected_sample_rms+c_corrected_sample_rms+d_corrected_sample_rms+e_corrected_sample_rms+f_corrected_sample_rms)/6.0
	
	a_sample = np.array(a_sample)-3.5
	b_sample = np.array(b_sample)-3.5
	c_sample = np.array(c_sample)-3.5
	d_sample = np.array(d_sample)-3.5
	e_sample = np.array(e_sample)-3.5
	f_sample = np.array(f_sample)-3.5
	
	a_sample_rms = np.sqrt(np.mean(np.square(a_sample)))
	b_sample_rms = np.sqrt(np.mean(np.square(b_sample)))
	c_sample_rms = np.sqrt(np.mean(np.square(c_sample)))
	d_sample_rms = np.sqrt(np.mean(np.square(d_sample)))
	e_sample_rms = np.sqrt(np.mean(np.square(e_sample)))
	f_sample_rms = np.sqrt(np.mean(np.square(f_sample)))
	avg_sample_rms = (a_sample_rms+b_sample_rms+c_sample_rms+d_sample_rms+e_sample_rms+f_sample_rms)/6.0
	
	"""
	############################################
	# Build up matrix to write to file
	write_matrix = [[0 for x in range(7)] for x in range(num_samples)]
	file_loc = "/home/user/data/TISC%d/GLITC_%d/impulse_only_study/Event_data"%(TISC,GLITC_n)
	filename = datetime+"_impulse_only.dat"
	
	for i in range(num_samples):
		write_matrix[i][0] = time[i]
		write_matrix[i][1] = a_sample[i]
		write_matrix[i][2] = b_sample[i]
		write_matrix[i][3] = c_sample[i]
		write_matrix[i][4] = a_corrected_sample[i]
		write_matrix[i][5] = b_corrected_sample[i]
		write_matrix[i][6] = c_corrected_sample[i]
		
	write_to_file(file_loc,filename,write_matrix)
	###############################################
	"""
	
	
	# For plotting noise
	plt.figure(1,figsize=(16,9))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_sample,label=("RMS: %1.2f"%(a_sample_rms)))
	plt.plot(time,b_sample,label=("RMS: %1.2f"%(b_sample_rms)))
	plt.plot(time,c_sample,label=("RMS: %1.2f"%(c_sample_rms)))
	#plt.show()
	#plt.plot(time,d_sample,label=("RMS: %1.2f"%(d_sample_rms)))
	#plt.plot(time,e_sample,label=("RMS: %1.2f"%(e_sample_rms)))
	#plt.plot(time,f_sample,label=("RMS: %1.2f"%(f_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC 0 Uncorrected Impulse")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC_Output [DAC]")
	#plt.legend()
	#plt.show()
	#plt.clf()
	#plt.close()
	
	plt.figure(2,figsize=(16,9))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_mean_corrected_sample,label=("RMS: %1.2f"%(a_mean_corrected_sample_rms)))
	plt.plot(time,b_mean_corrected_sample,label=("RMS: %1.2f"%(b_mean_corrected_sample_rms)))
	plt.plot(time,c_mean_corrected_sample,label=("RMS: %1.2f"%(c_mean_corrected_sample_rms)))
	#plt.plot(time,d_mean_corrected_sample,label=("RMS: %1.2f"%(d_mean_corrected_sample_rms)))
	#plt.plot(time,e_mean_corrected_sample,label=("RMS: %1.2f"%(e_mean_corrected_sample_rms)))
	#plt.plot(time,f_mean_corrected_sample,label=("RMS: %1.2f"%(f_mean_corrected_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC 0 Mean Corrected Impulse")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC_Output [DAC]")
	#plt.legend()
	#plt.show()
	#plt.clf()
	#plt.close()
	
	plt.figure(3,figsize=(16,9))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_corrected_sample,label=("RMS: %1.2f"%(a_corrected_sample_rms)))
	plt.plot(time,b_corrected_sample,label=("RMS: %1.2f"%(b_corrected_sample_rms)))
	plt.plot(time,c_corrected_sample,label=("RMS: %1.2f"%(c_corrected_sample_rms)))
	#plt.plot(time,d_corrected_sample,label=("RMS: %1.2f"%(d_corrected_sample_rms)))
	#plt.plot(time,e_corrected_sample,label=("RMS: %1.2f"%(e_corrected_sample_rms)))
	#plt.plot(time,f_corrected_sample,label=("RMS: %1.2f"%(f_corrected_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC 0 INL Corrected Impulse")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	#plt.legend()
	#plt.show()
	#plt.clf()
	#plt.close()
	
	plt.figure(4,figsize=(16,9))
	#plt.plot(available_time_window,available_window)
	abc_add = np.add(a_corrected_sample,np.add(b_corrected_sample,c_corrected_sample))
	def_add = np.add(d_corrected_sample,np.add(f_corrected_sample,e_corrected_sample))
	abcdef_add = np.add(abc_add,def_add)
	plt.plot(time,abc_add)
	plt.plot(time,def_add)
	
	plt.figure(5,figsize=(16,9))
	plt.plot(time,abcdef_add)
	#plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, INL Corrected Thermal Noise ("+datetime+")")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	plt.legend()
	plt.show()
	plt.clf()
	plt.close()
	
	print "Average uncorrected RMS: %1.2f"%avg_sample_rms
	print "Average Mean corrected RMS: %1.2f"%avg_mean_corrected_rms
	print "Average INL corrected RMS: %1.2f"%avg_corrected_rms
	print "Mean correction percent improvment: %1.2f"%(100*(avg_sample_rms-avg_mean_corrected_rms)/avg_sample_rms)
	print "INL correction percent improvment: %1.2f"%(100*(avg_sample_rms-avg_corrected_rms)/avg_sample_rms)
	
	
	#plot_array_average = np.average(plot_array)
	
	a_power = np.square(a_corrected_sample)
	
	sample_fft = fft(a_power)

	sample_fft/=num_samples/2
	frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
	#max_frequency_bin = np.argmax(2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	#print frequency[max_frequency_bin]

	
	plt.figure(figsize=[16,12])
	#plt.axvline(x=input_freq,linestyle="--",color='r',label=("Input Frequency: %dMHz"%(input_freq/1000000)))
	#plt.plot(frequency[1:num_samples/2]/10**6,2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	plt.hist(frequency[1:num_samples/2],100,range=[0,1400000000],log=True,weights=abs(sample_fft[1:num_samples/2]))
	#plt.ylim((0,0.5))
	plt.title("Thermal Power Spectrum")
	#plt.title("Impulse Test")
	plt.xlabel("Frequency [MHz]")
	plt.ylabel("Amplitude")
	plt.legend()
	plt.grid(True)
	#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (TISC,GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	#plt.show()
	#plt.clf()
	plt.close()
	
	return None


def RITC_storage_3ch_save_datatable(GLITC,GLITC_n,RITC, input_SNR, ped_dac=730,atten_dac=16,num_reads=255,num_trials=1):

	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	
	
	reload(tsd)
	reload(tisc)
	for ch_i in range(RITC*4,RITC*4+3):
		print "Setting channel %d thresholds" % ch_i
		set_thresholds(GLITC,GLITC_n,ch_i)
	
		if(GLITC.dac(ch_i)!=ped_dac):
			sleep(0.01)
			GLITC.dac(ch_i,ped_dac)
			sleep(5)
			
		if(GLITC.atten(ch_i)!=atten_dac):
			sleep(0.01)
			GLITC.atten(ch_i,atten_dac)
			sleep(5)
		
	a_offsets = get_individual_sample_offsets(GLITC_n,RITC*4)
	b_offsets = get_individual_sample_offsets(GLITC_n,RITC*4+1)
	c_offsets = get_individual_sample_offsets(GLITC_n,RITC*4+2)
		
	for trial in range(num_trials):	
		print "Starting trial # %d"%trial
		
		datetime = strftime("%Y_%M_%d_%H:%m:%S")
		
		time = np.linspace(0,time_step*num_samples,num_samples)*10**9
		a_sample,b_sample,c_sample = GLITC.RITC_storage_read_3ch(RITC,num_reads=num_reads*2)
		sleep(0.01)

		a_corrected_sample = do_glitch_correction(a_sample)
		b_corrected_sample = do_glitch_correction(b_sample)
		c_corrected_sample = do_glitch_correction(c_sample)

		# Individual Sample Correction
		a_corrected_sample = np.array(correct_individual_samples(a_corrected_sample,a_offsets))-3.5
		b_corrected_sample = np.array(correct_individual_samples(b_corrected_sample,b_offsets))-3.5
		c_corrected_sample = np.array(correct_individual_samples(c_corrected_sample,c_offsets))-3.5
	
		a_sample = np.array(a_sample)-3.5
		b_sample = np.array(b_sample)-3.5
		c_sample = np.array(c_sample)-3.5
		
		############################################
		# Build up matrix to write to file
		write_matrix = [[0 for x in range(7)] for x in range(num_samples+1)]
		
		#correlated_sum,abc_add,abc_add_rounded,abc_square = perform_GLITC_ops(a_corrected_sample,b_corrected_sample,c_corrected_sample)
		#corrected_square_peak_position, corrected_square_impulse_ptp, corrected_square_impulse_sum, corrected_square_noise_rms, corrected_square_noise_sum, corrected_square_SNR, corrected_correlated_sum = do_SNR_analysis(abc_square,time)
		
		file_loc = "/home/user/data/TISC%d/GLITC_%d/Pulse_data/SNR_%1.2f"%(TISC,GLITC_n, input_SNR)
		if not os.path.exists(file_loc):
			os.makedirs(file_loc)
		filename = "SNR"+str(input_SNR)+"_trial_"+str(trial)+".dat"
		
		write_matrix[0] = ["# "+datetime,"GLITC #"+str(GLITC_n),"RITC #"+str(RITC),"Ped Dac: "+str(ped_dac),"Atten_dac: "+str(atten_dac),0,0,0]

		for i in range(num_samples):
			write_matrix[i+1][0] = time[i]
			write_matrix[i+1][1] = a_sample[i]
			write_matrix[i+1][2] = b_sample[i]
			write_matrix[i+1][3] = c_sample[i]
			write_matrix[i+1][4] = a_corrected_sample[i]
			write_matrix[i+1][5] = b_corrected_sample[i]
			write_matrix[i+1][6] = c_corrected_sample[i]
			

		write_to_file(file_loc,filename,write_matrix)
		
	return None#corrected_square_SNR, corrected_square_impulse_sum, corrected_square_noise_sum, corrected_correlated_sum


def RITC_storage_6ch_save_datatable(GLITC,GLITC_n, input_atten, ped_dac=730,atten_dac=2,num_reads=255,num_trials=1,start_trial = 0):

	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	
	atten_array = [2,4,0,2,0,3]
	#atten_array = [0,4,0,2,0,1]
	for ch_i in range(7):
		if(ch_i==3):
			continue
		print "Setting channel %d thresholds" % ch_i
		set_thresholds(GLITC,GLITC_n,ch_i)
	
		if(GLITC.dac(ch_i)!=ped_dac):
			sleep(0.01)
			GLITC.dac(ch_i,ped_dac)
			sleep(5)
	for ch_i in range(6):		
		if(GLITC.atten(ch_i)!=atten_dac+atten_array[ch_i]):
			sleep(0.01)
			print "Setting channel %d attenuation" % ch_i
			GLITC.atten(ch_i,atten_dac+atten_array[ch_i])
			sleep(5)
			sleep(0.01)
			GLITC.atten(ch_i,atten_dac+atten_array[ch_i])
			sleep(5)
		
	a_offsets = get_individual_sample_offsets(GLITC_n,0)
	b_offsets = get_individual_sample_offsets(GLITC_n,1)
	c_offsets = get_individual_sample_offsets(GLITC_n,2)
	
	d_offsets = get_individual_sample_offsets(GLITC_n,4)
	e_offsets = get_individual_sample_offsets(GLITC_n,5)
	f_offsets = get_individual_sample_offsets(GLITC_n,6)
		
	for trial in range(start_trial, num_trials):	
		current_time = strftime("%H:%M:%S")
		print "Starting trial # %d at %s"%(trial,current_time)
		
		datetime = strftime("%Y_%m_%d_%H:%M:%S")
		
		time = np.linspace(0,time_step*num_samples,num_samples)*10**9
		a_sample,b_sample,c_sample,d_sample,e_sample,f_sample = GLITC.RITC_storage_read_6ch(num_reads=num_reads*2)
		sleep(0.01)
		
		#current_time = strftime("%H:%M:%S")
		#print "Done reading out data from RITC at %s"%(current_time)
		
		a_corrected_sample = do_glitch_correction(a_sample)
		b_corrected_sample = do_glitch_correction(b_sample)
		c_corrected_sample = do_glitch_correction(c_sample)
		d_corrected_sample = do_glitch_correction(d_sample)
		e_corrected_sample = do_glitch_correction(e_sample)
		f_corrected_sample = do_glitch_correction(f_sample)

		# Individual Sample Correction
		a_corrected_sample = np.array(correct_individual_samples(a_corrected_sample,a_offsets))-3.5
		b_corrected_sample = np.array(correct_individual_samples(b_corrected_sample,b_offsets))-3.5
		c_corrected_sample = np.array(correct_individual_samples(c_corrected_sample,c_offsets))-3.5
		d_corrected_sample = np.array(correct_individual_samples(d_corrected_sample,d_offsets))-3.5
		e_corrected_sample = np.array(correct_individual_samples(e_corrected_sample,e_offsets))-3.5
		f_corrected_sample = np.array(correct_individual_samples(f_corrected_sample,f_offsets))-3.5
	
		a_sample = np.array(a_sample)-3.5
		b_sample = np.array(b_sample)-3.5
		c_sample = np.array(c_sample)-3.5
		d_sample = np.array(d_sample)-3.5
		e_sample = np.array(e_sample)-3.5
		f_sample = np.array(f_sample)-3.5
		
		#current_time = strftime("%H:%M:%S")
		#print "Done correcting data at %s"%(current_time)
		
		############################################
		# Build up matrix to write to file
		write_matrix = [[0 for x in range(13)] for x in range(num_samples+1)]
		
		#correlated_sum,abc_add,abc_add_rounded,abc_square = perform_GLITC_ops(a_corrected_sample,b_corrected_sample,c_corrected_sample)
		#corrected_square_peak_position, corrected_square_impulse_ptp, corrected_square_impulse_sum, corrected_square_noise_rms, corrected_square_noise_sum, corrected_square_SNR, corrected_correlated_sum = do_SNR_analysis(abc_square,time)
		
		file_loc = "/home/user/data/TISC%d/GLITC_%d/Pulse_data/Atten_%1.2f"%(TISC,GLITC_n, input_atten)
		if not os.path.exists(file_loc):
			os.makedirs(file_loc)
		filename = "Atten_"+str(input_atten)+"_trial_"+str(trial)+".dat"
		
		write_matrix[0] = ["# "+datetime,"GLITC #"+str(GLITC_n),"Ped Dac: "+str(ped_dac),"Atten_dac: "+str(atten_dac),0,0,0,0,0,0,0,0,0]

		for i in range(num_samples):
			write_matrix[i+1][0] = time[i]
			write_matrix[i+1][1] = a_sample[i]
			write_matrix[i+1][2] = b_sample[i]
			write_matrix[i+1][3] = c_sample[i]
			write_matrix[i+1][4] = d_sample[i]
			write_matrix[i+1][5] = e_sample[i]
			write_matrix[i+1][6] = f_sample[i]
			write_matrix[i+1][7] = a_corrected_sample[i]
			write_matrix[i+1][8] = b_corrected_sample[i]
			write_matrix[i+1][9] = c_corrected_sample[i]
			write_matrix[i+1][10] = d_corrected_sample[i]
			write_matrix[i+1][11] = e_corrected_sample[i]
			write_matrix[i+1][12] = f_corrected_sample[i]
			

		write_to_file(file_loc,filename,write_matrix)
		#current_time = strftime("%H:%M:%S")
		#print "Finished at %s"%(current_time)
		
	return None#corrected_square_SNR, corrected_square_impulse_sum, corrected_square_noise_sum, corrected_correlated_sum


def RITC_storage_6ch_plotter(GLITC_n,input_atten, start_trial = 0, num_trials = 1):

	file_loc = "/home/user/data/TISC%d/GLITC_%d/Pulse_data/Atten_%1.2f"%(TISC,GLITC_n, input_atten)
	if not os.path.exists(file_loc):
		print "ERROR! FILE DOES NOT EXIST!"
		return 0
	for trial_i in range(start_trial, start_trial+num_trials):
		
		time_array = []
		a_sample = []
		b_sample = []
		c_sample = []
		d_sample = []
		e_sample = []
		f_sample = []
		a_corrected_sample = []
		b_corrected_sample = []
		c_corrected_sample = []
		d_corrected_sample = []
		e_corrected_sample = []
		f_corrected_sample = []
		
		#with open("/home/user/data/TISC%d/GLITC_%d/Pulse_data/bad_trials/Atten_%d_trial_%d.dat"%(TISC,GLITC_n, input_atten, trial_i),'rb') as datafile:
		with open("/home/user/data/TISC%d/GLITC_%d/Pulse_data/Atten_%1.2f/Atten_%d_trial_%d.dat"%(TISC,GLITC_n, input_atten, input_atten, trial_i),'rb') as datafile:
			datareader = csv.reader(datafile, delimiter=',', quotechar='|')
		
			row_number = 0
			header_flag = 0

			# Read in and plot the data
			for row in datareader:
			
				if (header_flag == 0):
					header_flag = 1
				else:			
					time_array.append(float(row[0]))
					a_sample.append(float(row[1]))
					b_sample.append(float(row[2]))
					c_sample.append(float(row[3]))
					d_sample.append(float(row[4]))
					e_sample.append(float(row[5]))
					f_sample.append(float(row[6]))
					a_corrected_sample.append(float(row[7]))
					b_corrected_sample.append(float(row[8]))
					c_corrected_sample.append(float(row[9]))
					d_corrected_sample.append(float(row[10]))
					e_corrected_sample.append(float(row[11]))
					f_corrected_sample.append(float(row[12]))
		time_array = np.array(time_array)
		a_sample = np.array(a_sample)
		b_sample = np.array(b_sample)
		c_sample = np.array(c_sample)
		d_sample = np.array(d_sample)
		e_sample = np.array(e_sample)
		f_sample = np.array(f_sample)
		a_corrected_sample = np.array(a_corrected_sample)
		b_corrected_sample = np.array(b_corrected_sample)
		c_corrected_sample = np.array(c_corrected_sample)
		d_corrected_sample = np.array(d_corrected_sample)
		e_corrected_sample = np.array(e_corrected_sample)
		f_corrected_sample = np.array(f_corrected_sample)
		
		time_step = time_array[2]-time_array[1]
		num_samples = len(time_array)
		
		plt.plot(time_array,a_corrected_sample,label=('channel 1'))
		plt.plot(time_array,b_corrected_sample,label=('channel 2'))
		plt.plot(time_array,c_corrected_sample,label=('channel 3'))
		plt.plot(time_array,d_corrected_sample,label=('channel 4'))
		plt.plot(time_array,e_corrected_sample,label=('channel 5'))
		plt.plot(time_array,f_corrected_sample,label=('channel 6'))
	
		plt.title("GLITC %d, Input Atten %d " % (GLITC_n,input_atten))
		plt.xlabel("Time [ns]")
		plt.ylabel("Corrected Output Value")
		plt.legend()
		#plt.grid(True)
		#plt.ylim((0,7))
		#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sine_study/%dMHz_sine_atten_%1.2fdB.png" % (TISC,GLITC_n,input_freq/1000000,atten_db)))
		plt.show()
		plt.close()
		"""
		#DO ALL THE FFTS!!!
		a_corrected_average = np.average(a_corrected_sample)
		b_corrected_average = np.average(b_corrected_sample)
		c_corrected_average = np.average(c_corrected_sample)
		d_corrected_average = np.average(d_corrected_sample)
		e_corrected_average = np.average(e_corrected_sample)
		f_corrected_average = np.average(f_corrected_sample)
		#print corrected_sample_average
	
		a_sample_fft = fft(a_corrected_sample-a_corrected_average)
		b_sample_fft = fft(b_corrected_sample-b_corrected_average)
		c_sample_fft = fft(c_corrected_sample-c_corrected_average)
		d_sample_fft = fft(d_corrected_sample-d_corrected_average)
		e_sample_fft = fft(e_corrected_sample-e_corrected_average)
		f_sample_fft = fft(f_corrected_sample-f_corrected_average)
		
		frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
		max_frequency_bin = np.argmax(2.0/num_samples*np.abs(a_sample_fft[1:num_samples/2]))
		print "Channel 1 max frequency=" + str(frequency[max_frequency_bin] )
	
		plt.figure(figsize=[16,12])
		plt.plot(frequency,2.0/num_samples*np.abs(a_sample_fft[0:num_samples/2]),label=('channel 1'))
		plt.plot(frequency,2.0/num_samples*np.abs(b_sample_fft[0:num_samples/2]),label=('channel 2'))
		plt.plot(frequency,2.0/num_samples*np.abs(c_sample_fft[0:num_samples/2]),label=('channel 3'))
		plt.plot(frequency,2.0/num_samples*np.abs(d_sample_fft[0:num_samples/2]),label=('channel 4'))
		plt.plot(frequency,2.0/num_samples*np.abs(e_sample_fft[0:num_samples/2]),label=('channel 5'))
		plt.plot(frequency,2.0/num_samples*np.abs(f_sample_fft[0:num_samples/2]),label=('channel 6'))
		#plt.ylim((0,2.5))
		plt.title("FFT of pulse")#%(input_freq/1000000))
		plt.title("FFT of pulse")
		plt.xlabel("Frequency [GHz]")
		plt.ylabel("Amplitude")
		plt.legend()
		plt.grid(True)
		#plt.savefig(("/home/user/data/TISC%d/GLITC_%d/sine_study/%dMHz_sine_fft_atten_%1.2fdB.png" % (TISC,GLITC_n,input_freq/1000000,atten_db)))
		plt.show()
		#plt.clf()
		plt.close()
		"""
		
		del time_array
		del a_sample
		del b_sample
		del c_sample
		del d_sample 
		del e_sample 
		del f_sample 
		del a_corrected_sample
		del b_corrected_sample
		del c_corrected_sample
		del d_corrected_sample
		del e_corrected_sample
		del f_corrected_sample
		
	return None
	

def do_SNR_analysis(sample_array,time,window_width=1000,sum_width=182):
	
	sample_length = len(sample_array)
	
	available_time_window = np.array(time[window_width/2+1:sample_length-window_width/2-1])
	
	available_window = np.array(sample_array[window_width/2+1:sample_length-window_width/2-1])
	#print sample_array
	high_peak_position = window_width/2+1+available_window.argmax()
	low_peak_position = window_width/2+1+available_window.argmin()
	
	
	if(abs(sample_array[high_peak_position])>=abs(sample_array[low_peak_position])):
		peak_position = high_peak_position
	else:
		peak_position = low_peak_position
	
	impulse_ptp = sample_array[high_peak_position]-sample_array[low_peak_position]
	impulse_sum = np.sum(sample_array[peak_position-sum_width/2:peak_position+sum_width/2])
	
	
	noise_rms = np.sqrt(np.mean(np.square(sample_array[peak_position-window_width/2:peak_position-100])))
	noise_sum = np.sum(sample_array[peak_position-100-sum_width:peak_position-100])
	SNR = impulse_ptp/(2*noise_rms)
	
	sample_sum = np.sum(sample_array[peak_position-window_width/2:peak_position+window_width/2])
	
	return peak_position,impulse_ptp,impulse_sum,noise_rms,noise_sum,SNR,sample_sum


def do_glitch_correction(sample):
	
	return_sample = np.copy(sample)
	
	# 4-3 Glitch correction
	for i in range(0,len(sample)-1):
		if(sample[i]==7 and sample[i+1]<=4):
			return_sample[i] = 4
	return return_sample


def run_correction_vs_noncorrection_study(GLITC,GLITC_n,RITC,num_trials=2,num_reads=100):

	c_sqr_SNR = np.zeros(num_trials)
	c_sqr_imp_sum = np.zeros(num_trials)
	c_sqr_noise_sum = np.zeros(num_trials)
	c_sqr_corr_sum = np.zeros(num_trials)
	uc_sqr_SNR = np.zeros(num_trials)
	uc_sqr_imp_sum = np.zeros(num_trials)
	uc_sqr_noise_sum = np.zeros(num_trials)
	uc_sqr_corr_sum = np.zeros(num_trials)

	for i in range(num_trials):
		print "Running trial %d"%i
		c_sqr_SNR[i],c_sqr_imp_sum[i],c_sqr_noise_sum[i],c_sqr_corr_sum[i],uc_sqr_SNR[i],uc_sqr_imp_sum[i],uc_sqr_noise_sum[i],uc_sqr_corr_sum[i] = RITC_storage_impulse_only_3ch(GLITC,GLITC_n,RITC,num_reads=num_reads)
		
	c_sqr_SNR_mean = np.mean(c_sqr_SNR)
	c_sqr_imp_sum_mean = np.mean(c_sqr_imp_sum)
	c_sqr_noise_sum_mean = np.mean(c_sqr_noise_sum)
	c_sqr_corr_sum_mean = np.mean(c_sqr_corr_sum)
	c_sqr_SNR_std = np.std(c_sqr_SNR)
	c_sqr_imp_sum_std = np.std(c_sqr_imp_sum)
	c_sqr_noise_sum_std = np.std(c_sqr_noise_sum)
	c_sqr_corr_sum_std= np.std(c_sqr_corr_sum)

	uc_sqr_SNR_mean = np.mean(uc_sqr_SNR)
	uc_sqr_imp_sum_mean = np.mean(uc_sqr_imp_sum)
	uc_sqr_noise_sum_mean = np.mean(uc_sqr_noise_sum)
	uc_sqr_corr_sum_mean = np.mean(uc_sqr_corr_sum)
	uc_sqr_SNR_std = np.std(uc_sqr_SNR)
	uc_sqr_imp_sum_std = np.std(uc_sqr_imp_sum)
	uc_sqr_noise_sum_std = np.std(uc_sqr_noise_sum)
	uc_sqr_corr_sum_std= np.std(uc_sqr_corr_sum)
	
	print "Corrected SNR: %1.2f +- %1.2f"%(c_sqr_SNR_mean,c_sqr_SNR_std)
	print "Uncorrected SNR: %1.2f +- %1.2f\n"%(uc_sqr_SNR_mean,uc_sqr_SNR_std)
	print "Corrected Impulse Sum: %1.2f +- %1.2f"%(c_sqr_imp_sum_mean,c_sqr_imp_sum_std)
	print "Uncorrected Impulse Sum: %1.2f +- %1.2f\n"%(uc_sqr_imp_sum_mean,uc_sqr_imp_sum_std)
	print "Corrected Noise Sum: %1.2f +- %1.2f"%(c_sqr_noise_sum_mean,c_sqr_noise_sum_std)
	print "Uncorrected Noise Sum: %1.2f +- %1.2f\n"%(uc_sqr_noise_sum_mean,uc_sqr_noise_sum_std)
	print "Corrected Correlation Sum: %1.2f +- %1.2f"%(c_sqr_corr_sum_mean,c_sqr_corr_sum_std)
	print "Uncorrected Correlation Sum: %1.2f +- %1.2f\n"%(uc_sqr_corr_sum_mean,uc_sqr_corr_sum_std)

	
def run_individual_sample_correction_study():
	
	for GLITC_n in range(4):
		GLITC = setup(GLITC_n)
		
		for ch_i in range(7):
			
			if(ch_i==3):
				continue
			
			set_thresholds(GLITC,GLITC_n,ch_i)
			
			pedestal_vs_sample_scan(GLITC,GLITC_n,ch_i)
	
	return None


def write_to_file(file_loc,filename,array):
		
	with open((str(file_loc)+'/'+str(filename)),'wb') as f:
		writer = csv.writer(f)
		for i in range(len(array)):
			writer.writerow(array[i])	
	
		
	return None
