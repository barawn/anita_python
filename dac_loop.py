import ocpci
import struct
import sys
import tisc
from time import sleep
import numpy as np
from mpl_toolkits.mplot3d import Axes3D
from matplotlib import cm
from matplotlib.ticker import LinearLocator, FormatStrFormatter, MaxNLocator
import matplotlib.pyplot as plt
#from mayavi import mlab


dev = tisc.TISC()

wait_time = 0.01
vdd_counter = 0
vss_counter = 0
step_value = 100
start_value = 0
end_value = 4096
num_index = int((end_value-start_value)/step_value) +1

for GLITC_n in range(0,4):

	if (GLITC_n == 0):		
		GLITC = dev.GA
	elif (GLITC_n == 1):		
		GLITC = dev.GB
	elif (GLITC_n == 2):		
		GLITC = dev.GC
	elif (GLITC_n == 3):		
		GLITC = dev.GD
	

	print "Starting run on GLITC "+str(GLITC_n)

	#counter = np.empty((num_index,num_index,6))
	#vss = np.empty((num_index,num_index,6))
	#vdd = np.empty((num_index,num_index,6))

	vss_counter=0

	f = open("/home/user/data/GLITC_"+str(GLITC_n)+"/ref_clk_dac.dat","w")


	GLITC.datapath_input_ctrl(1)

	# Enable VCDL in R0 & R1
	GLITC.vcdl(1,1)
	sleep(wait_time)

	GLITC.vcdl(0,1)
	sleep(wait_time)


	for k in range(start_value,end_value,step_value):
		vdd_counter = 0
		print "Setting Vss to "+str(hex(k))
		
		GLITC.rdac(0,32,k)
		sleep(wait_time)
		
		GLITC.rdac(1,32,k)
		sleep(wait_time)
		
		# Loop over each possible value for Vdd
		for i in range(start_value,end_value,step_value):
			clock_counter = 0
			
			GLITC.rdac(0,31,i)
			sleep(wait_time)
				
			GLITC.rdac(1,31,i)
			sleep(wait_time)
		
			#pull counter for the 6 clock references.
			# 0-2 are for DAC 0, 3-5 are for DAC 1
			for j in range(0x00000,0x60000,0x10000):
				#print clock_counter
				GLITC.write((0x23)*4,j)
				sleep(wait_time)
				#counter[vss_counter][vdd_counter][clock_counter] = GLITC.read((0x23)*4) & 0xFFFF
				counter_tmp = GLITC.read((0x23)*4) & 0xFFFF
				sleep(wait_time)
				#vss[vss_counter][vdd_counter][j] = k
				#vdd[vss_counter][vdd_counter][j] = i
				f.write(str(k)+",\t"+str(i)+",\t"+str(clock_counter)+",\t"+str(counter_tmp)+"\n")
				clock_counter += 1
				
			vdd_counter += 1
			
		vss_counter += 1	
				
				
			
			#if counter != 0:
			#	print "Found a non-zero ref clk!"
			#	print "Vss Value: " +str(hex(i))
			#	print "Vdd Value: " +str(hex(k))
			#	print "Counter Value: "+str(counter)
			#	print "Ref Clock Adr: "+str(hex(j))
				
	# Disable VCDL in R0 & R1
	GLITC.write((0x21)*4,0x0)
	sleep(wait_time)


	f.close()

	# Start plot section here
	#print "Plot section Initiated."
	#for i in range(0,6):
		#fig = plt.figure()
		#ax = fig.gca(projection='3d')
		#X = np.arange(start_value, end_value, step_value)
		#Y = np.arange(start_value, end_value, step_value)
		#X, Y = np.meshgrid(X, Y)
		#counter_tmp = counter[:,:,i]
		#Z = counter_tmp
		#surf = ax.plot_surface(X, Y, Z, rstride=1, cstride=1, cmap=cm.coolwarm,
			#linewidth = 0, antialiased=False)
		#ax.view_init(azim = 180+40,elev=22)
		#ax.set_zlim(0,1000)
		#fig.colorbar(surf, shrink=0.5, aspect=5)

		#ax.xaxis.set_major_locator( MaxNLocator(5) )
		#ax.yaxis.set_major_locator( MaxNLocator(5) )

		#plt.title("Ref Clock "+str(i)+" surface plot")
		#ax.set_xlabel("  Vss")
		#ax.set_ylabel("  Vdd")
		#ax.set_zlabel("\nCounter")
		#if (i < 3):
			#plt.savefig("/home/user/data/GLITC_"+str(GLITC_n)+"/RITC_0/Ref_Clock_"+str(i)+"_surface_plot.png")
		#if (i >= 3):
			#plt.savefig("/home/user/data/GLITC_"+str(GLITC_n)+"/RITC_1/Ref_Clock_"+str(i)+"_surface_plot.png")

		#plt.show()


