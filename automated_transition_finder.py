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
import tisc_toolbox as ttb

def find_threshold_offsets():

	wait_time = 0.01

	transition_values = [2048,1024,1536,1792]
	
	sample_number = 0
	for GLITC_n in range(7):

		GLITC = ttb.setup(GLITC_n)
		
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
			
			with open('/home/user/data/GLITC_'+str(GLITC_n)+'/transition_study/GLITC_'+str(GLITC_n)+'_channel_'+str(channel)+'_transition_offsets_4.dat','wb') as f:
				writer = csv.writer(f)
				writer.writerow(['GLITC','channel','threshold_dac_number','threshold_label','transition','input_dac_value','sample_number','offset','rough_offset','previous_rms_error','rms_error','next_rms_error','clean_transition_flag'])
				pp = PdfPages('/home/user/data/GLITC_'+str(GLITC_n)+'/transition_study/G'+str(GLITC_n)+'_CH'+str(channel)+'_transitions_4.pdf')
			#if(True):	
				
				#pp = None
				for threshold_level_i in range(7):
					threshold_label = 7-threshold_level_i
					
					
					# Get the DAC numbers
					"""
					if (channel<= 2):
						RITC_COMP = ((channel*7)+threshold_level_i)
					elif (channel >2):
						RITC_COMP = ((channel-4)*7)+threshold_level_i
					"""
					RITC,RITC_COMP = ttb.get_channel_info(channel,threshold_label)
					
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
						input_dac_transition_value,sample_transition_value,sample_number = ttb.find_bit_transition_all_samples(GLITC,GLITC_n,channel,RITC,RITC_COMP,transition_value,threshold_label,sample_number,pp)
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
						
						threshold_array,sample_array,transition_value_index = ttb.transition_threshold_scan(GLITC,GLITC_n,channel,RITC,RITC_COMP,input_dac_transition_value,transition_value,threshold_label,sample_number,pp)
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
						offset,rough_offset,previous_rms_error,rms_error,next_rms_error,offset_method = ttb.find_best_offset(GLITC,channel,threshold_label,sample_number,sample_array,transition_value,transition_value_index)
							
						
						
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
					
						
						ttb.make_scatter_plot(pp,graph_3_x,graph_3_y,GLITC_n,channel,threshold_label,transition_value,input_dac_transition_value,offset,sample_number,2)
				
				if(pp!=None):
					pp.close()
				
if __name__ == "__main__":
	
	find_threshold_offsets()
					


