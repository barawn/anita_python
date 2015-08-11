import tisc_toolbox as ttb
import tisc
from time import sleep
import matplotlib.pyplot as plt
import matplotlib.cm as cm
import numpy as np
from scipy.stats import norm
from matplotlib.backends.backend_pdf import PdfPages
import csv

min_input = 400
max_input = 1400
step_input = 40
num_input_steps = int((max_input-min_input)/step_input)+1
input_array = [0]*num_input_steps

min_threshold_range = 500
max_threshold_range = 3500 
threshold_step = 10
num_trials = 1

input_midpoint = 760

file_iterator = "5_exteneded_high_end"

for GLITC_i in range(4):
	
	GLITC = ttb.setup(GLITC_i)
	
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
			pp = PdfPages('/home/user/data/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_transition_histogram_%s.pdf'%(GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator))
			ppp = PdfPages('/home/user/data/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_transition_line_%s.pdf'%(GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator))
			
			RITC,RITC_COMP = ttb.get_channel_info(channel_i,threshold_label)
			GLITC.reset_all_thresholds(RITC,0)
			
			# Set higher threshold to maximum
			for threshold_level_ii in range(0,threshold_level_i):
				print "Setting comparator %d to max" % (RITC_COMP-threshold_level_ii-1)
				GLITC.rdac(RITC,RITC_COMP-threshold_level_ii-1,4095)
						
			with open('/home/user/data/GLITC_%d/threshold_study/G%d_Ch%d_Th%d_%s.dat'%(GLITC_i,GLITC_i,channel_i,threshold_label,file_iterator),'wb') as f:
				writer = csv.writer(f)
				writer.writerow(['Input_DAC','Threshold_DAC','Sample','Output'])
			#if(True):
				#pp = None
				#ppp = None
				
				threshold_transition_mean = []
				threshold_transition_sigma = []
				input_array_temp = []
								
				
				for input_dac_i in range(min_input,max_input+1,step_input):
					colors = iter(cm.brg(np.linspace(0,1,32)))
	
					print "Setting input DAC to %d (%1.2f mV)" % (input_dac_i,input_dac_i*2500./4095.)
					GLITC.dac(channel_i,input_dac_i)
					sleep(5)
					
					print "Starting threshold scan"
					sample_array,threshold_array = ttb.threshold_scan_all_samples(GLITC,GLITC_i,channel_i,threshold_label,num_trials,min_threshold_range,max_threshold_range,threshold_step)
	
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
					

					(mu, sigma) = norm.fit(transition_point)
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
						
					if(threshold_label==7 and full_sigma<=200):
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
		
		
		if(working_range_end-input_midpoint<=input_midpoint-working_range_start):
			delta_working_range = working_range_end-input_midpoint
			working_input_range = np.linspace(input_midpoint-delta_working_range,working_range_end,7)
		else:
			delta_working_range = input_midpoint-working_range_start
			working_input_range = np.linspace(working_range_start,input_midpoint+delta_working_range,7)
		
		#working_input_range = np.linspace(working_range_start,working_range_end,7)
		print "Working input range "+str(working_input_range)
		threshold_settings = [0]*7
		for threshold_i in range(7):
			threshold_label = 7-threshold_i
			threshold_settings[threshold_i] = mean_fit[0]*working_input_range[threshold_i]**2+mean_fit[1]*working_input_range[threshold_i]+mean_fit[2]
			
		print "Threshold settings "+str(threshold_settings)
			
		with open('/home/user/data/GLITC_%d/threshold_study/G%d_Ch%d_settings_%s.dat'%(GLITC_i,GLITC_i,channel_i,file_iterator),'wb') as f:
				writer = csv.writer(f)
				writer.writerow(['GLITC','Channel'])
				writer.writerow([GLITC_i,channel_i])
				writer.writerow(['Input range'])
				writer.writerow(working_input_range)
				writer.writerow(['Fit parameters [a,b,c] for ax^2+bx+c'])
				writer.writerow(mean_fit)
				writer.writerow(['Threshold settings'])
				writer.writerow(threshold_settings)
		
					
				
