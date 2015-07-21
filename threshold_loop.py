import ocpci
import struct
import sys
import tisc
from time import sleep, time
import numpy as np
import csv
import datetime


def read_all_samples(glitc, channel,wait_time=0.01):
	sample_values = [0]*32
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		#sleep(wait_time)
		sample_values[sample_i]=trans[glitc.train_read(channel, sample_i, 1)]
		#sleep(wait_time)
	return sample_values
	
def read_all_samples_n(glitc, channel,num_trials):
	sample_values = [0]*32
	
	# Flip the bit order.
	trans = [0,4,2,6,1,5,3,7]
	for sample_i in range(0,32):
		for n in range(num_trials):
			sample_values[sample_i]+=trans[glitc.train_read(channel, sample_i, 1)]

	#sample_values = sample_values/num_trials
	return sample_values
	
def reset_all_thresholds(glitc,RITC,reset_value=4095,wait_time=0.01):
	# Reset all thresholds to the highest value
	for i in range(21):
		sleep(wait_time)
		GLITC.rdac(RITC,i,4095)
		#sleep(wait_time)

dev = tisc.TISC()

wait_time = 0.01

sample_values = []

for i in range(32):
	sample_values.append([])




starttime = time()
for GLITC_n in range(0,1):#:4):
	
	# Initialize the data path and set the Vdd & Vss points
	if (GLITC_n == 0):
		#print "starting glitc 0"		
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
	
	
	

	print "Starting threshold/pedistal scan on GLITC "+str(GLITC_n)

	#loop over each channel, note our channel here goes left to right on the board.
	for channel_i in range(1,7):#,7):
		if (channel_i==3):
			continue
		if (channel_i <= 2):
			RITC = 0
		elif (channel_i >2):
			RITC = 1
		
			
		#datafile = open('/home/user/data/GLITC_'+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/Fine/channel_'+str(channel_i)+'_threshold_data_ultrafine.dat','w')
		#datafile.write('GLITC,Channel,Threshold_DAC,Threshold_dac_value,Pedestal_dac_value,sample_values_0_to_31\n')
		with open('/home/user/data/GLITC_'+str(GLITC_n)+'/RITC_'+str(RITC)+'/Ch_'+str(channel_i)+'/channel_'+str(channel_i)+'_threshold_data_bit_1536_transition_test_long.dat','wb') as f:
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
					


