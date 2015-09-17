
import matplotlib.pyplot as plt
import tisc
from time import sleep, strftime
import numpy as np
import TISC_transition_offsets_dictionary as tod
import TISC_threshold_setting_dictionary as tsd
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages
from scipy.optimize import leastsq
from scipy.fftpack import fft
import csv
import matplotlib.gridspec as gridspec
from scipy.stats import norm
import math
import os

def setup(GLITC_n,wait_time=0.01):
	    
	# Initialize the data path and set the Vdd & Vss points
	if (GLITC_n == 0):
		print "starting glitc 0"		
		GLITC = tisc.TISC().GA
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1725)
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
		print "starting glitc 1"		
		GLITC = tisc.TISC().GB
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		#GLITC.rdac(0,31,1645) # Old value
		GLITC.rdac(0,31,1670) # initial value
		#GLITC.rdac(0,31,2033)
		sleep(wait_time)
		GLITC.rdac(0,32,3500) # initial value
		sleep(wait_time)
		#GLITC.rdac(1,31,1765) # Old value
		GLITC.rdac(1,31,1750)
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
		print "starting glitc 2"		
		GLITC = tisc.TISC().GC
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1740)
		sleep(wait_time)
		GLITC.rdac(0,32,3500)
		sleep(wait_time)
		GLITC.rdac(1,31,2060) # Initial value
		#GLITC.rdac(1,31,2157) # Found during timing study
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
		print "starting glitc 3"	
		GLITC = tisc.TISC().GD
		GLITC.datapath_initialize()
		sleep(wait_time)
		GLITC.write(0x40,0x1)
		sleep(wait_time)
		GLITC.rdac(0,31,1755)
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
	else:
		print "Invalid GLITC number!"
		return 1
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
	
	
	
	sample_array = []

	
	for thres_i in range(7):
		threshold_label = 7-thres_i
		RITC, RITC_COMP = get_channel_info(channel,threshold_label)
		threshold_value = tsd.get_threshold(10002,GLITC_n,channel,RITC_COMP)
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
	
	#RITC,RITC_COMP = get_channel_infor(channel,threshold_label)
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
			
		
	#make_scatter_plot(pp,graph_1_x,graph_1_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,0)
	
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
	plt.show()
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

	
	"""
	num_trials = 100 
	rough_offset = offset
	rms_error = [0]*3
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
			for i in range(num_trials):
				sample_at+=GLITC.scaler_read(channel,sample_number)/1023.0/float(threshold_label)
			sample_at/=float(num_trials)
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
				
				for i in range(num_trials):
					sample_before+=GLITC.scaler_read(channel,sample_number)/1023.0/float(threshold_label)
				sample_before/=float(num_trials)
				#print "sample at: %1.2f" % sample_at
				#print "sample before: %1.2f" % sample_before
				#print threshold_label
				if (sample_before < 0.22  or sample_before > 0.78):
					#(sample_at-0.05)
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
				return rough_offset,rough_offset,4095,4095,4095
			
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
					for i in range(num_trials):
						sample_after[j+1]+=GLITC.scaler_read(channel,sample_number)/1023./float(threshold_label)
					sample_after[j+1]/=float(num_trials)
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
		if(np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[2]**2) and delta_plus[1]*delta_minus >=0):
			break
		#elif (np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[1]**2)<=np.sqrt(rms_error[2]**2) and delta_plus[1]*delta_minus <= 0):	
			#offset+=10
		elif(np.sqrt(rms_error[1]**2)>=np.sqrt(rms_error[0]**2) and np.sqrt(rms_error[0]**2)<=np.sqrt(rms_error[2]**2)):
			offset-=1
		elif(np.sqrt(rms_error[1]**2)>=np.sqrt(rms_error[2]**2) and np.sqrt(rms_error[2]**2)<=np.sqrt(rms_error[0]**2)):
			offset+=1
		if(offset<min_offset):
			offset=min_offset
			break
	"""	
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
	#plt.savefig('/home/user/data/GLITC_'+str(GLITC_n)+'/timing_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_sample'+str(sample_number)+'_vss_study_6')
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
	#plt.savefig('/home/user/data/GLITC_'+str(GLITC_n)+'/timing_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_sample'+str(sample_number)+'_vdd_study')
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
			pp = PdfPages('/home/user/data/GLITC_'+str(GLITC_n)+'/sample_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_sample_study_2.pdf')
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
	#plt.savefig('/home/user/data/GLITC_'+str(GLITC_n)+'/sample_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_TH'+str(threshold_label)+'_input'+str(input_dac_value)+'_2.png')
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
	offset_2048,offset_1024,offset_512,offset_256,offset_128 = tod.get_offsets(10002,GLITC_n,channel,RITC_DAC_Number)
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
	#plt.savefig(("/home/user/data/GLITC_%d/sine_study/%dMHz_sine_atten_%1.2fdB.png" % (GLITC_n,input_freq/1000000,atten_db)))
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
	#plt.savefig(("/home/user/data/GLITC_%d/sine_study/%dMHz_sine_fft_atten_%1.2fdB.png" % (GLITC_n,input_freq/1000000,atten_db)))
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
	plt.savefig(("/home/user/data/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_atten_%1.2fdB.png" % (GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
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
	#plt.savefig(("/home/user/data/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
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

	reload(tsd)
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
		plt.savefig(("/home/user/data/GLITC_%d/G%d_Ch%d_sample%d_ped_only.png" % (GLITC_n,GLITC_n,channel,samp_i)))
		plt.clf()
	plt.show()
	"""
	datafile_array = [0]*2
	
	with open('/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only_2.dat'%(GLITC_n,channel,GLITC_n,channel),'wb') as f:
		writer = csv.writer(f)
		writer.writerow(['Ped_DAC','Avg_Sample','Samples_0_to_31'])
		for i in range(num_peds):
			datafile_array[0] = ped_array[i]
			datafile_array[1] = average_sample[i]
			writer.writerow(np.concatenate((datafile_array,sample_array[:,i])))
	
	
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
	
	with open('/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only.dat'%(GLITC_n,GLITC_n,channel,channel),'rb') as datafile:
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
		#plt.savefig(("/home/user/data/GLITC_%d/sample_study/channel _%d/G%d_Ch%d_sample%d_ped_only.png" % (GLITC_n,channel,GLITC_n,channel,samp_i)))
		#plt.clf()
		"""
		best_rms_error,best_offset,rms_corrected_sample_array = minimize_RMS_error(sample_array[samp_i],ideal_line,offset_min,offset_max,offset_step)
		rms_corrected_residuals = np.subtract(rms_corrected_sample_array,ideal_line)
		rms_corrected_residuals = np.sqrt(rmse_bc**2-rms_corrected_residuals**2)
		
		fig = plt.figure(figsize=(16,12))
		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.1)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array,rms_corrected_sample_array,label=("Corrected Sample %d (RMSE %1.2f)"%(samp_i,best_rms_error)),color='b')
		#ax1.plot(ped_array,mean_corrected_sample_array,label=("Sample %d Mean"%samp_i))
		ax1.plot(ped_array,sample_array[samp_i],linestyle=":",color='b',label=("Non-corrected (RMSE %1.2f)"%rms_error))
		ax1.plot(ped_array,ideal_line,linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0)
		ax1.set_title("GLITC %d, Ch %d, Sample %d - RMS Corrected by %1.2f"%(GLITC_n,channel,samp_i,best_offset))
		ax1.set_ylabel("Averaged Output")
		
		#residuals = np.subtract(sample_array[samp_i],ideal_line)
		ax2.plot(ped_array,rms_corrected_residuals,label="Corrected Sample - Ideal")
		ax2.plot(ped_array,residuals,linestyle=":",color='b',label="Non-corrected")
		ax2.axhline(y=0,linestyle="--",color='r')
		ax2.set_xlabel("Pedestal DAC")
		ax2.legend(loc=3)
		#plt.show()
		plt.savefig(("/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample%d_ped_only_rmse_corrected.png" % (GLITC_n,channel,GLITC_n,channel,samp_i)))
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
	
	
	
	with open('/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_ped_only_2.dat'%(GLITC_n,channel,GLITC_n,channel),'rb') as datafile:
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
	
	#pp = PdfPages("/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_threshold_histograms.pdf" % (GLITC_n,channel,GLITC_n,channel))
	
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
			
			plt.figure(figsize=(16,12))
			plt.hist(hist[sample_i][thres_i],len(ped_array)/2,weights=weight[sample_i][thres_i],range=[np.amin(ped_array),np.amax(ped_array)],label=("Mu %1.2f"%mu))
			plt.axvline(mu)
			plt.xlim(np.amin(hist[sample_i][thres_i]),np.amax(hist[sample_i][thres_i]))
			plt.xlabel("Pedestal DAC")
			plt.title("GLITC %d, Ch %d, Sample %d, Threshold %d Histogram"%(GLITC_n,channel,sample_i,thres_i))
			#plt.savefig(pp, format='pdf')
			plt.show()
			plt.clf()
			
			sample_correction[sample_i] = np.add(plot_hist*offsets[sample_i][thres_i],sample_correction[sample_i])

	
		
		sample_corrected_array[sample_i] = np.add(sample_correction[sample_i],sample_array[sample_i])
		
	#pp.close()
	
	plt.figure(figsize=(16,12))	
	plt.hist(np.reshape(offsets,32*8),16)
	plt.title("GLITC %d, Ch %d Sample Offset Histogram"%(GLITC_n,channel))
	plt.xlabel("Offsets [threshold levels]")
	#plt.savefig(("/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_all_offsets_histogram.png" % (GLITC_n,channel,GLITC_n,channel)))
	plt.show()
	plt.clf()
	plt.close()
	
	"""
	# Save sample_threshold offsets
	with open('/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(GLITC_n,channel,GLITC_n,channel),'wb') as f:
		writer = csv.writer(f)
		for i in range(samples_per_vcdl):
			writer.writerow(offsets[i])
	"""
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
		#plt.savefig(("/home/user/data/GLITC_%d/sample_study/channel _%d/G%d_Ch%d_sample%d_ped_only.png" % (GLITC_n,channel,GLITC_n,channel,samp_i)))
		#plt.clf()
		"""
		best_rms_error,best_offset,rms_corrected_sample_array = minimize_RMS_error(sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index],offset_min,offset_max,offset_step)
		rms_corrected_residuals = np.subtract(rms_corrected_sample_array,ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		#rms_corrected_residuals = np.sqrt(abs(rmse_bc**2-rms_corrected_residuals**2))
		best_rms_error = np.sqrt(abs(rmse_bc**2-best_rms_error**2))
		
		ind_corr_rms_error = get_RMS_error(sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		ind_corr_residuals = np.subtract(sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index])
		ind_corr_rms_error = np.sqrt(abs(rmse_bc**2-ind_corr_rms_error**2))
		
		fig = plt.figure(figsize=(16,12))
		ax1 = fig.add_subplot(gs[:2,0])#, sharex=True)
		ax2 = fig.add_subplot(gs[2,0])
		fig.subplots_adjust(hspace=0.1)
		#ax1.plot(ped_array,average_sample,label="All sample average")
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],rms_corrected_sample_array,label=("Corrected Sample %d (RMSE %1.2f)"%(samp_i,best_rms_error)),color='b')
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],sample_corrected_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],label=("Ind. Corr. Sample %d (RMSE %1.2f)"%(samp_i,ind_corr_rms_error)),color='g')
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],sample_array[samp_i][rmse_low_bound_index:rmse_high_bound_index],linestyle=":",color='b',label=("Non-corrected (RMSE %1.2f)"%rms_error))
		ax1.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],ideal_line[rmse_low_bound_index:rmse_high_bound_index],linestyle="--",label=("Ideal Line"),color='r')
		ax1.legend(loc=0)
		ax1.set_title("GLITC %d, Ch %d, Sample %d Corrected Transfer Curves"%(GLITC_n,channel,samp_i))
		#ax1.set_title("GLITC %d, Ch %d, Sample %d Transfer Curve"%(GLITC_n,channel,samp_i))
		ax1.set_ylabel("Averaged Output")
		
		#residuals = np.subtract(sample_array[samp_i],ideal_line)
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],rms_corrected_residuals,label="RMS Corr.")
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],residuals,linestyle=":",color='b',label="Non-corrected")
		ax2.plot(ped_array[rmse_low_bound_index:rmse_high_bound_index],ind_corr_residuals,linestyle="-",color='g',label="Ind. Samp. corrected")
		ax2.axhline(y=0,linestyle="--",color='r')
		ax2.set_xlabel("Pedestal DAC")
		ax2.legend(loc=3)
		plt.show()
		#plt.savefig(("/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample%d_ped_only_ind_thres_corrected.png" % (GLITC_n,channel,GLITC_n,channel,samp_i)))
		plt.clf()
		plt.close()
	
	return None

# Read the individual sample offsets file and returns a 2d matrix [sample]x[threshold_level]
def get_individual_sample_offsets(GLITC_n,channel):
	
	offsets = [[0 for x in range(8)] for x in range(32)]
	row_counter = 0
	with open('/home/user/data/GLITC_%d/sample_study/channel_%d/G%d_Ch%d_sample_threshold_offsets.dat'%(GLITC_n,channel,GLITC_n,channel),'rb') as datafile:
		datareader = csv.reader(datafile, delimiter=',', quotechar='|')
		# Read in and plot the data
		for row in datareader:
			for thres_i in range(8):
				offsets[row_counter][thres_i] = float(row[thres_i])			
			row_counter+=1
	
	
	return offsets
	
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
	file_loc = "/home/user/data/GLITC_%d/impulse_only_study/Event_data"%GLITC_n
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
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(a_sample))))))
	plt.plot(time,b_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(b_sample))))))
	plt.plot(time,c_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(c_sample))))))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC %d, Uncorrected Samples No Inputs ("+datetime+")")%(GLITC_n,RITC))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC_Output [DAC]")
	plt.legend()
	#plt.show()
	plt.clf()
	plt.close()
	
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_corrected_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(a_corrected_sample))))))
	plt.plot(time,b_corrected_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(b_corrected_sample))))))
	plt.plot(time,c_corrected_sample,label=("RMS: %1.2f"%(np.sqrt(np.mean(np.square(c_corrected_sample))))))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, RITC %d, Corrected Samples No Inputs ("+datetime+")")%(GLITC_n,RITC))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	plt.legend()
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
	#plt.savefig(("/home/user/data/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	#plt.show()
	#plt.clf()
	#plt.close()
	#del corrected_sample
	#del sample
	"""
	return corrected_square_SNR, corrected_square_impulse_sum, corrected_square_noise_sum, corrected_correlated_sum, uncorrected_square_SNR, uncorrected_square_impulse_sum, uncorrected_square_noise_sum, uncorrected_correlated_sum


def sample_correction_comparison(GLITC,GLITC_n,ped_dac=730,atten_dac=16,num_reads=1):
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
	for ch_i in range(7):
		if(ch_i==3):
			continue
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
	file_loc = "/home/user/data/GLITC_%d/impulse_only_study/Event_data"%GLITC_n
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
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_sample,label=("RMS: %1.2f"%(a_sample_rms)))
	plt.plot(time,b_sample,label=("RMS: %1.2f"%(b_sample_rms)))
	plt.plot(time,c_sample,label=("RMS: %1.2f"%(c_sample_rms)))
	plt.plot(time,d_sample,label=("RMS: %1.2f"%(d_sample_rms)))
	plt.plot(time,e_sample,label=("RMS: %1.2f"%(e_sample_rms)))
	plt.plot(time,f_sample,label=("RMS: %1.2f"%(f_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, Uncorrected Thermal Noise ("+datetime+")")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC_Output [DAC]")
	plt.legend()
	#plt.show()
	plt.clf()
	plt.close()
	
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_mean_corrected_sample,label=("RMS: %1.2f"%(a_mean_corrected_sample_rms)))
	plt.plot(time,b_mean_corrected_sample,label=("RMS: %1.2f"%(b_mean_corrected_sample_rms)))
	plt.plot(time,c_mean_corrected_sample,label=("RMS: %1.2f"%(c_mean_corrected_sample_rms)))
	plt.plot(time,d_mean_corrected_sample,label=("RMS: %1.2f"%(d_mean_corrected_sample_rms)))
	plt.plot(time,e_mean_corrected_sample,label=("RMS: %1.2f"%(e_mean_corrected_sample_rms)))
	plt.plot(time,f_mean_corrected_sample,label=("RMS: %1.2f"%(f_mean_corrected_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, Mean Corrected Thermal Noise ("+datetime+")")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC_Output [DAC]")
	plt.legend()
	#plt.show()
	plt.clf()
	plt.close()
	
	plt.figure(figsize=(16,12))
	#plt.plot(available_time_window,available_window)
	plt.plot(time,a_corrected_sample,label=("RMS: %1.2f"%(a_corrected_sample_rms)))
	plt.plot(time,b_corrected_sample,label=("RMS: %1.2f"%(b_corrected_sample_rms)))
	plt.plot(time,c_corrected_sample,label=("RMS: %1.2f"%(c_corrected_sample_rms)))
	plt.plot(time,d_corrected_sample,label=("RMS: %1.2f"%(d_corrected_sample_rms)))
	plt.plot(time,e_corrected_sample,label=("RMS: %1.2f"%(e_corrected_sample_rms)))
	plt.plot(time,f_corrected_sample,label=("RMS: %1.2f"%(f_corrected_sample_rms)))
	plt.ylim([-3.5,3.5])
	plt.title(("GLITC %d, INL Corrected Thermal Noise ("+datetime+")")%(GLITC_n))
	plt.xlabel("time [ns]") 
	plt.ylabel("RITC Output [DAC]")
	plt.legend()
	#plt.show()
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
	print len(sample_fft)
	print num_samples
	#sample_fft/=num_samples/2
	frequency = np.linspace(0.0,1.0/(2.0*time_step),num_samples/2)
	
	max_frequency_bin = np.argmax(2.0/num_samples*np.abs(sample_fft[1:num_samples/2]))
	#print frequency[max_frequency_bin]
	bins = np.linspace(0,2000000000,10000000)
	
	plt.figure(figsize=[16,12])
	#plt.axvline(x=input_freq,linestyle="--",color='r',label=("Input Frequency: %dMHz"%(input_freq/1000000)))
	#plt.plot(frequency/10**6,2.0/num_samples*np.abs(sample_fft[0:num_samples/2]))
	plt.hist(2.0/num_samples*np.abs(sample_fft[0:num_samples/2]),bins)
	#plt.ylim((0,0.5))
	plt.title("Thermal Power Spectrum")
	#plt.title("Impulse Test")
	plt.xlabel("Frequency [MHz]")
	plt.ylabel("Amplitude")
	plt.legend()
	plt.grid(True)
	#plt.savefig(("/home/user/data/GLITC_%d/impulse_only_study/G%d_Ch%d_%dmV_p2p_impulse_fft_atten_%1.2fdB.png" % (GLITC_n,GLITC_n,channel,input_amp_p2p,atten_db)))
	plt.show()
	#plt.clf()
	#plt.close()
	
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
		
		file_loc = "/home/user/data/GLITC_%d/Pulse_data/SNR_%1.2f"%(GLITC_n, input_SNR)
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



def RITC_storage_6ch_save_datatable(GLITC,GLITC_n, input_atten, ped_dac=730,atten_dac=16,num_reads=255,num_trials=1):

	# Make sure GLITC is set up!!!!
	sample_frequency = 2600000000.0
	time_step = 1.0/sample_frequency
	samples_per_vcdl = 32
	num_samples = samples_per_vcdl*num_reads
	atten_db = atten_dac*0.25
	
	
	reload(tsd)
	reload(tisc)
	for ch_i in range(7):
		if (ch_i ==3):
			continue
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
		
	a_offsets = get_individual_sample_offsets(GLITC_n,0)
	b_offsets = get_individual_sample_offsets(GLITC_n,1)
	c_offsets = get_individual_sample_offsets(GLITC_n,2)
	
	d_offsets = get_individual_sample_offsets(GLITC_n,4)
	e_offsets = get_individual_sample_offsets(GLITC_n,5)
	f_offsets = get_individual_sample_offsets(GLITC_n,6)
		
	for trial in range(num_trials):	
		print "Starting trial # %d"%trial
		
		datetime = strftime("%Y_%M_%d_%H:%m:%S")
		
		time = np.linspace(0,time_step*num_samples,num_samples)*10**9
		a_sample,b_sample,c_sample,d_sample,e_sample,f_sample = GLITC.RITC_storage_read_6ch(num_reads=num_reads*2)
		sleep(0.01)

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
		
		############################################
		# Build up matrix to write to file
		write_matrix = [[0 for x in range(13)] for x in range(num_samples+1)]
		
		#correlated_sum,abc_add,abc_add_rounded,abc_square = perform_GLITC_ops(a_corrected_sample,b_corrected_sample,c_corrected_sample)
		#corrected_square_peak_position, corrected_square_impulse_ptp, corrected_square_impulse_sum, corrected_square_noise_rms, corrected_square_noise_sum, corrected_square_SNR, corrected_correlated_sum = do_SNR_analysis(abc_square,time)
		
		file_loc = "/home/user/data/GLITC_%d/Pulse_data/Atten_%1.2f"%(GLITC_n, input_atten)
		if not os.path.exists(file_loc):
			os.makedirs(file_loc)
		filename = "SNR"+str(input_SNR)+"_trial_"+str(trial)+".dat"
		
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
		
	return None#corrected_square_SNR, corrected_square_impulse_sum, corrected_square_noise_sum, corrected_correlated_sum


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
	
	for GLITC_n in range(3,4):
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
