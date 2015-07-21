import matplotlib.pyplot as plt
import tisc
from time import sleep
import numpy as np
import TISC_transition_offsets_dictionary as tod
import matplotlib.cm as cm
from matplotlib.backends.backend_pdf import PdfPages

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


def input_dac_scan(GLITC_n,channel,threshold=1900,num_scans=1,dac_min=780,dac_max=820,threshold_label=4,sample_number=0,pp=None,num_trials=10,wait_time=0.01):
	
	#dac_min = 780
	#dac_max = 820
	
	RITC, RITC_COMP = get_channel_info(channel,threshold_label)
	
	GLITC = setup(GLITC_n)
	
	GLITC.reset_all_thresholds(RITC,0)
	
	print "RITC COMP: %d" % RITC_COMP
	print "RITC: %d" % RITC
	
	# Set higher threshold to maximum
	for threshold_level_ii in range(0,7-threshold_label):
		print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
		GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
	
	GLITC.rdac(RITC,RITC_COMP,threshold)
	sleep(5)
	
	colors = iter(cm.brg(np.linspace(0,1,dac_max-dac_min)))
	plt.figure(figsize=(16,12))	
		
	#for scan_i in range(num_scans):
	#print scan_i
	sample_value_array = np.zeros(32)

	offset_flag = 0
	previous_sample = 1.0
	offset=0
	input_array = []
	sample_array = []
	inside_flag = 0
	outside_flag = 1
	midpoint_counter = 0

	for input_i in range(dac_min,dac_max):
		#print "Setting threshold to %1.1d (%1.2fmV)" % (thres_i, thres_i*1200./4095.)
		# Step threshold dac value
		print "Setting input to: %d" % input_i
		GLITC.dac(channel,input_i)
		sleep(5)

		sample_value = 0.0
		# Read in samples and check if it passes the sample transition point
		sample_value = GLITC.scaler_read(channel,sample_number,num_trials)
		if(sample_value>=0.4 and sample_value<=0.6 and inside_flag!=1):
			inside_flag = 1
			outside_flag = 0
			midpoint_counter+=1
		if((sample_value<0.4 or sample_value>0.6) and outside_flag!=1):
			inside_flag = 0
			outside_flag = 1
			midpoint_counter+=1
		
		input_array.append(input_i)
		sample_array.append(sample_value)
		
	plt.plot(input_array,sample_array)#,color=next(colors),label=("Input DAC: %d" % input_i))
	#make_scatter_plot(pp,threshold_array,sample_array,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,0,sample_number,1)	
	plt.title("GLITC "+str(GLITC_n)+", Ch "+str(channel)+", Threshold "+str(threshold_label)+", Sample Number "+str(sample_number))
	plt.xlabel("Input Voltage (DAC Counts)")
	plt.ylabel("Normalized Output Value")
	plt.legend()
	plt.text(dac_max-2,threshold_label-0.5, ('Threshold DAC: %1.1d' % threshold), fontsize = 18)
	#plt.axis([transition_value-150,transition_value+150,2.8,7])
	#plt.savefig('/home/user/data/GLITC_'+str(GLITC_n)+'/transition_study/G'+str(GLITC_n)+'_CH'+str(channel)+' sample'+str(sample_number)+'_vss_study_4')
	plt.show()
	#return threshold_array,sample_array,transition_value_index,midpoint_counter
	return 0


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


def stitch_threshold_dac(GLITC_n,channel,RITC_DAC_Number,dac):
	dac_temp = dac
	"""
	offset_2048 = 54
	offset_1024 = 47
	offset_512 = 18
	offset_256 = 0
	offset_128 = 0
	"""
	offset_2048,offset_1024,offset_512,offset_256,offset_128 = tod.get_offsets(10002,GLITC_n,channel,RITC_DAC_Number)
	pre_point_offset = offset_1024+2*offset_512+4*offset_256+8*offset_128
	if(dac>2047-pre_point_offset):
		dac+=offset_2048+pre_point_offset
		dac_temp-=2048+pre_point_offset
		
	pre_point_offset = offset_512+2*offset_256+4*offset_128
	if(dac_temp>1023-pre_point_offset):
		dac+=offset_1024+pre_point_offset
		dac_temp-=1024+pre_point_offset
	
	pre_point_offset = offset_256+2*offset_128
	if(dac_temp>511-pre_point_offset):
		dac+=offset_512+pre_point_offset
		dac_temp-=512+pre_point_offset
	
	pre_point_offset = offset_128
	if(dac_temp>255-pre_point_offset):
		dac+=offset_256+pre_point_offset
		dac_temp-=256+pre_point_offset
	
	pre_point_offset = 0
	if(dac_temp>127-pre_point_offset):
		dac+=offset_128+pre_point_offset
		dac_temp-=128+pre_point_offset
	return dac
	
	
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
