import ocpci
import struct
import sys
import time
from bf import *
import spi

#
# Bitfield manipulation. Note that ordering
# can be Python (smallest first) or Verilog
# (largest first) for easy compatibility
#


class mapDevice:
    def __init__(self):
        return
    def regprint(self, name):
        print hex(self.read(self.map[name]))
    
    def regwrite(self, name, value):
        self.write(self.map[name], value)
    
    def regread(self, name):
        return self.read(self.map[name])
		
class PicoBlaze:
    instr0_map = { (0x00>>1) : "LOAD",
                   (0x16>>1) : "STAR",
                   (0x02>>1) : "AND",
                   (0x04>>1) : "OR",
                   (0x06>>1) : "XOR",
                   (0x10>>1) : "ADD",
                   (0x12>>1) : "ADDCY",
                   (0x18>>1) : "SUB",
                   (0x1A>>1) : "SUBCY",
                   (0x0C>>1) : "TEST",
                   (0x0E>>1) : "TESTCY",
                   (0x1C>>1) : "COMPARE",
                   (0x1E>>1) : "COMPARECY" }
    instr1_map = { 0x06 : "SL0",
                   0x07 : "SL1",
                   0x04 : "SLX",
                   0x00 : "SLA",
                   0x02 : "RL",
                   0x0E : "SR0",
                   0x0F : "SR1",
                   0x0A : "SRX",
                   0x08 : "SRA",
                   0x0C : "RR",
                   0x80 : "HWBUILD"}
    instr2_map = { (0x08>>1) : "INPUT",
                   (0x2C>>1) : "OUTPUT",
                   (0x2E>>1) : "STORE",
                   (0x0A>>1) : "FETCH" }
    def __init__(self, dev, addr):
        self.dev = dev
        self.addr = addr

    def __repr__(self):
        return "<PicoBlaze in dev:%r at 0x%8.8x>" % (self.dev, self.addr)

    def __str__(self):
        return "PicoBlaze (@%8.8x)" % self.addr

    def read(self, addr = None):
        val = bf(self.dev.read(self.addr))
        oldval = val
        if addr is not None:
            val[27:18] = addr
            val[30] = 0
            self.dev.write(self.addr, int(val))
            val = bf(self.dev.read(self.addr))
            self.dev.write(self.addr, int(oldval))
        return "%3.3x: %s [%s]" % (val[27:18],self.decode(val[17:0]),"RESET" if val[31] else "RUNNING")

    def program(self, path):
        oldctrl = bf(self.dev.read(self.addr))
        # 'addr' points to the BRAM control register
        ctrl = bf(0)
        # set processor_reset
        ctrl[31] = 1
        self.dev.write(self.addr, int(ctrl))
        # enable BRAM WE
        ctrl[30] = 1
        bramaddr=0
        with open(path,"rb") as f:        
            for line in f:
                instr = int(line, 16)
                if bramaddr == 0:
                    print "PicoBlaze address 0 (reset) instruction: %8.8x" % instr
                ctrl[17:0] = instr
                ctrl[27:18] = bramaddr
                self.dev.write(self.addr, int(ctrl))
                bramaddr = bramaddr + 1
                if bramaddr > 1023:
                    break
        print oldctrl[31]
        if oldctrl[31] == 1:
            print "Leaving PicoBlaze in reset."
        else:
            print "Pulling PicoBlaze out of reset."
            ctrl = 0
            self.dev.write(self.addr, int(ctrl))
        print "PicoBlaze address 0 (reset) readback: %8.8x" % (self.dev.read(self.addr) & 0xFFFFFFFF)        
        
        
    @staticmethod
    def decode(val):
        instr = bf(val)
        instr0 = PicoBlaze.instr0_map.get(instr[17:13])
        if instr0 is not None:
            return "%s s%1.1X, %s" % ( instr0, instr[11:8], format(instr[7:0], 'X') if instr[12] else ("s%1.1X" % instr[7:4]))
        else:
            # Shift/rotate/hwbuild instructions.
            if instr[17:12] == 0x14:
                instr1 = PicoBlaze.instr1_map.get(instr[7:0])
                if instr1 is not None:
                    return "%s s%1.1X" % (instr1, instr[11:8])
                else:
                    return "Illegal instruction."
            # Jump/call instructions.
            elif instr[17:16] == 0x3 and instr[12] == 0:
                return "%s %s%s, %3.3x" % ( "JUMP" if instr[13] else "CALL", "N" if instr[14] else "", "C" if instr[15] else "Z", instr[11:0])
            elif instr[17:12] == 0x22 or instr[17:12] == 0x20:
                return "%s %3.3x" % ( "JUMP" if instr[13] else "CALL", instr[11:0] )
            elif instr[17:12] == 0x24 or instr[17:12] == 0x26:
                return "%s@ (s%1.1X,s%1.1X)" % ( "JUMP" if instr[13] else "CALL", instr[11:8], instr[7:4])
            # Return.
            # 11 0001
            # 11 0101
            # 11 1001
            # 11 1101
            elif instr[17:16] == 0x3 and instr[12:11] == 1:
                return "RETURN %s%s" % ( "N" if instr[14] else "", "C" if instr[15] else "Z")
            elif instr[17:12] == 0x25:
                return "RETURN"
            # In/out/store/fetch
            elif instr[17:13] == (0x08>>1) or instr[17:13] == (0x2C>>1) or instr[17:13] == (0x2E>>1) or instr[17:13] == (0x0A>>1):
                return "%s s%1.1X, %s" % ( PicoBlaze.instr2_map[instr[17:13]], instr[11:8], format(instr[7:0],'X') if instr[12] else ("(s%1.1X)"%instr[7:4]))
            elif instr[17:12] == 0x2B:
                return "OUTPUTK %2.2x, %2.2x" % (instr[11:4], instr[3:0])
            # Specialty
            elif instr[17:12] == 0x37:
                return "REGBANK %s" % ("B" if instr[0] else "A")
            elif instr[17:13] == (0x28>>1):
                return "%s%s%s" % ( "RETURNI " if instr[12] else "", "ENABLE" if instr[0] else "DISABLE", "" if instr[12] else " INTERRUPT")
            elif instr[17:12] == 0x21:
                return "LOAD&RETURN s%1.1X, %2.2X" % (instr[11:8], instr[7:0])

class GLITC:
    map = { 'ident'          : 0x000000,
            'ver'            : 0x000004,
            'control'        : 0x000008,
            'SERIAL'         : 0x00000C,
            'DPCTRL0'        : 0x000080,
            'DPCTRL1'        : 0x000084,
            'DPTRAINING'     : 0x000088,
            'DPCOUNTER'      : 0x00008C,
            'DPIDELAY'       : 0x000090,
            'DPSCALER'		 : 0x000094,
            'STORCTRL'		 : 0x0000C0,
            'RDINPUT'        : 0x000100,
            'RDCTRL'         : 0x000104,
            'settings_dac'   : 0x000140,
            'settings_atten' : 0x000160,
            'settings_sc'    : 0x000178,
            'settings_pb'    : 0x00017C,
            'phasescan_pb'   : 0x000058,
            'GICTRL0'        : 0x000180,
            'GICTRL1'        : 0x000184,
            'GITRAINUP'      : 0x000188,
            'GITRAINDOWN'    : 0x00018C,
            'STORCTL'        : 0x0000C0,
            'SAMPDATA'       : 0x004000,
            'RITC_STORAGE'   : 0x008000}
            
    def __init__(self, dev, base):
        self.dev = dev
        self.base = base
        self.settings_pb = PicoBlaze(self, self.map['settings_pb'])
        self.phasescan_pb = PicoBlaze(self, self.map['phasescan_pb'])
        
    def __repr__(self):
        return "<GLITC in dev:%r at 0x%8.8x>" % (self.dev, self.base)

    def __str__(self):
        return "GLITC (@%8.8x)" % self.base

    def status(self):
        ctrl = bf(self.read(self.map['control']))
        print "Clock status (%8.8x)   : SYSCLK = REFCLK%s" % (int(ctrl)&0xFFFFFFFF, "" if ctrl[0] else "x6.5")
        print "                          : 6.5x MMCM is %spowered down" % ("" if ctrl[1] else "not ")
        print "                          : MMCMs are %sin reset" % ("" if ctrl[2] else "not ")
        ctrl = bf(self.read(self.map['DPCTRL0']))
        print "Datapath status (%8.8x): FIFO is %senabled" % (int(ctrl)&0xFFFFFFFF, "" if ctrl[1] else "not ")
        print "                          : DELAYCTRL is %sready" % ("" if ctrl[4] else "not ")
        print "                          : Datapath inputs are %senabled" % ("not " if ctrl[5] else "")
        ctrl = bf(self.read(self.map['DPCTRL1']))
        print "VCDL status (%8.8x)    : REFCLK R0, CH0 is %s" % (int(ctrl)&0xFFFFFFFF, "high" if ctrl[16] else "low")
        print "                          : REFCLK R0, CH1 is %s" % ("high" if ctrl[17] else "low")
        print "                          : REFCLK R0, CH2 is %s" % ("high" if ctrl[18] else "low")
        print "                          : REFCLK R1, CH0 is %s" % ("high" if ctrl[19] else "low")
        print "                          : REFCLK R1, CH1 is %s" % ("high" if ctrl[20] else "low")
        print "                          : REFCLK R1, CH2 is %s" % ("high" if ctrl[21] else "low")
        print "                          : R0 VCDL is %srunning" % ("" if ctrl[29] else "not ")
        print "                          : R1 VCDL is %srunning" % ("" if ctrl[31] else "not ")
        ctrl = bf(self.read(self.map['DPTRAINING']))
        print "Training status (%8.8x): Training is %s" % (int(ctrl)&0xFFFFFFFF, "off" if ctrl[31] else "on")
        print "                          : Training is in %s view" % ("sample" if ctrl[29] else "signal")
        print "                          : Training latch is %senabled" % ("" if ctrl[28] else "not ")	
	
	
    def datapath_input_ctrl(self, enable):
        val = bf(self.read(self.map['DPCTRL0']))
        if enable == 0:
            val[5] = 1
        else:
            val[5] = 0
        print "Going to write %8.8x" % int(val)
        self.write(self.map['DPCTRL0'], int(val))

    def datapath_initialize(self):
        self.datapath_input_ctrl(1)
        # Do something here about checking polarity
        # of REFCLK. Turn off VCDL first, then
        # check polarity, invert if needed, and restart.
        self.vcdl(0, 1)
        self.vcdl(1, 1)
        # Maybe do something here about autotuning?
        self.fifo_ctrl(0)
        self.serdes_reset()
        self.fifo_reset()
        self.fifo_ctrl(1)
        
    def serdes_reset(self):
        val = bf(self.read(self.map['DPCTRL0']))
        val[2] = 1
        self.write(self.map['DPCTRL0'], int(val))
    
    def fifo_reset(self):
        val = bf(self.read(self.map['DPCTRL0']))
        val[0] = 1
        self.write(self.map['DPCTRL0'], int(val))
        
    def fifo_ctrl(self, en):
        val = bf(self.read(self.map['DPCTRL0']))
        val[1] = en
        self.write(self.map['DPCTRL0'], int(val))

    def vcdl_pulse(self, channel):
        if channel > 1:
            print "Illegal RITC channel (%d)" % channel
            return
        val = bf(self.read(self.map['DPCTRL1']))
        if channel == 0:
            val[28] = 1
        else:
            val[30] = 1
        self.write(self.map['DPCTRL1'], int(val))

    def counters(self):
        val = bf(0)
        for i in range(6):
            val[19:16] = i
            self.write(self.map['DPCOUNTER'], int(val))
            time.sleep(0.1)
            v2 = bf(self.read(self.map['DPCOUNTER']))
            print "Channel %d: %d" % (i, v2[15:0])

    def vcdl(self, channel, value = None):
        if channel > 1:
            print "Illegal RITC channel (%d)" % channel
            return None
        if value is None:
            val = bf(self.read(self.map['DPCTRL1']))
            if channel == 0:
                return 1 if val[29] else 0
            else:
                return 1 if val[31] else 0
        else:
            val = bf(self.read(self.map['DPCTRL1']))
            if channel == 0:
                val[29] = value
            else:
                val[31] = value
            self.write(self.map['DPCTRL1'], int(val))
            return value
            
    def delay_VCDL(self, channel, value = None):
        if channel > 1:
            print "Illegal RITC channel (%d)" % channel
            return None
        val = bf(self.read(self.map['DPCTRL1']))
        if channel == 0:
            val[5] = 1
            val[4:0] = value
        else:
            val[13] = 1
            val[12:8] = value
        self.write(self.map['DPCTRL1'], int(val))
            
    def train_latch_ctrl(self, en):
        val = bf(self.read(self.map['DPTRAINING']))
        val[28] = en
        self.write(self.map['DPTRAINING'], int(val))
            
    def training_ctrl(self, en):
        val = bf(self.read(self.map['DPTRAINING']))
        if en == 0:
            val[31] = 1
        else:
            val[31] = 0
        self.write(self.map['DPTRAINING'], int(val))
        
    def train_read(self, channel, bit_or_sample, sample_view=0):
        val = bf(self.read(self.map['DPTRAINING']))
        smp = bf(bit_or_sample)
        val[28] = 1
        val[29] = sample_view
        val[19:16] = smp[3:0]
        val[23] = smp[4]
        val[22:20] = channel
        self.write(self.map['DPTRAINING'], int(val))
        v2 = bf(self.read(self.map['DPTRAINING']))
        return v2[7:0]
    
    #This may be outdated and no longer work?
    def RITC_storage_read_6ch(self,addr_in=0,num_reads=1):
        addr = bf(0)
        data = bf(0)
        
        value_array_1 = []
        value_array_2 = []
        value_array_3 = []
        value_array_4 = []
        value_array_5 = []
        value_array_6 = []
        
        #print "Reading from channel %d"%channel
        if (num_reads>=512):
            print "Too many reads. Please enter number less than 512."
            return 1
        
        
        start_channel = 0
        
                   
        
        
        # Clear the block RAM
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        
        # Fill the block RAM
        self.write(self.map['STORCTRL'],0x1)
        time.sleep(0.1)
        
        # Read the block RAM as many times as needed
        for ch_i in range(start_channel,start_channel+6):
            addr[12:10]=ch_i
            addr[9:1]=addr_in
            temp_array = []
            self.write(self.map['RITC_STORAGE']+int(addr)*4,0x0)
            for read_i in range(num_reads):
			    #self.read(self.map['RITC_STORAGE']
			    value0 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4))
			    time.sleep(0.01)
			    for i in range(8):
				    sample_start = int(3*i)
				    sample_end = int(sample_start+2)
				    temp_array.append(value0[sample_end:sample_start])
			
			    value1 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4)) 
			    time.sleep(0.01)	
			    for i in range(8):
				    sample_start = int(3*i)
				    sample_end = int(sample_start+2)
				    temp_array.append(value1[sample_end:sample_start])
            
            if(ch_i == 0):
			    value_array_1 = temp_array
            elif(ch_i == 1):
                value_array_2 = temp_array
            elif(ch_i == 2):
                value_array_3 = temp_array
            elif(ch_i == 3):
			    value_array_4 = temp_array
            elif(ch_i == 4):
                value_array_5 = temp_array
            elif(ch_i == 5):
                value_array_6 = temp_array
                
            #print temp_array[0]
            
        # Clear the block RAM again
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        return value_array_1, value_array_2,value_array_3, value_array_4,value_array_5,value_array_6
    
    #This may be outdated?
    def RITC_storage_read_3ch(self,RITC,addr_in=0,num_reads=1):
        addr = bf(0)
        data = bf(0)
        
        value_array_1 = []
        value_array_2 = []
        value_array_3 = []
        
        #print "Reading from channel %d"%channel
        if (num_reads>=512):
            print "Too many reads. Please enter number less than 512."
            return 1
        
        if(RITC<1):
            start_channel = 0
        else:
            start_channel = 3
                   
        
        
        # Clear the block RAM
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        
        # Fill the block RAM
        self.write(self.map['STORCTRL'],0x1)
        time.sleep(0.1)
        
        # Read the block RAM as many times as needed
        for ch_i in range(start_channel,start_channel+3):
            addr[12:10]=ch_i
            addr[9:1]=addr_in
            temp_array = []
            self.write(self.map['RITC_STORAGE']+int(addr)*4,0x0)
            for read_i in range(num_reads):
			    #self.read(self.map['RITC_STORAGE']
			    value0 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4))
			    time.sleep(0.01)
			    for i in range(8):
				    sample_start = int(3*i)
				    sample_end = int(sample_start+2)
				    temp_array.append(value0[sample_end:sample_start])
			
			    value1 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4)) 
			    time.sleep(0.01)	
			    for i in range(8):
				    sample_start = int(3*i)
				    sample_end = int(sample_start+2)
				    temp_array.append(value1[sample_end:sample_start])
            
            if(ch_i ==0 or ch_i == 3):
				value_array_1 = temp_array
            elif(ch_i == 1 or ch_i ==4):
                value_array_2 = temp_array
            else:
                value_array_3 = temp_array
            
        # Clear the block RAM again
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        return value_array_1, value_array_2,value_array_3
    
    #This may be outdated
    def RITC_storage_read(self,channel,addr_in=0,num_reads=1):
        addr = bf(0)
        data = bf(0)
        value_array = []
        #print "Reading from channel %d"%channel
        if (num_reads>=512):
            print "Too many reads. Block ram only holds 512."
            return 1
        
        if(channel>=7 or channel==3):
            print "Invalid channel [0,1,2,4,5,6]"
            return 1
        elif(channel>3):
            channel-=1
                   
        addr[12:10]=channel
        addr[9:1]=addr_in
        
        # Clear the block RAM
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        
        # Fill the block RAM
        self.write(self.map['STORCTRL'],0x1)
        time.sleep(0.1)
        
        # Read the block RAM as many times as needed
        for read_i in range(num_reads):
			#self.read(self.map['RITC_STORAGE']
            value0 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4))
            time.sleep(0.01)
            for i in range(8):
                sample_start = int(3*i)
                sample_end = int(sample_start+2)
                value_array.append(value0[sample_end:sample_start])
            
            value1 = bf(self.read(self.map['RITC_STORAGE']+int(addr)*4)) 
            time.sleep(0.01)	
            for i in range(8):
                sample_start = int(3*i)
                sample_end = int(sample_start+2)
                value_array.append(value1[sample_end:sample_start])
            
        # Clear the block RAM again
        self.write(self.map['STORCTRL'],0x4)
        time.sleep(0.01)
        return value_array
        

    def eye_autotune_all(self):
        for i in (0,1,2,4,5,6):
            for j in xrange(12):
                self.eye_autotune(i,j)
    
    # I should believe in exceptions, really I should.
    def eye_autotune(self, channel, bit, verbose=1):
        eyevars = self.eye_scan(channel, bit, verbose)
        if eyevars[0] == 0:
            print "eye_autotune error: eye start not found (%2.2x %2.2x %2.2x)" % eyevars
            return -1
        elif eyevars[2] != 0x2B and eyevars[2] != 0x95 and eyevars[2] != 0xCA and eyevars[2] != 0x65:
            print "eye_autotune error: unknown value in eye (%2.2x %2.2x %2.2x)" % eyevars
            return -1
        eyecenter = (eyevars[1] + eyevars[0])/2
        self.delay(channel, bit, int(eyecenter))
        bitslip_count = 0
        if eyevars[2] == 0x2B:
            bitslip_count = 2
        elif eyevars[2] == 0x95:
            bitslip_count = 1
        elif eyevars[2] == 0x65:
            bitslip_count = 3
        if verbose == 1:
            print "eye_autotune: setting to delay %d" % eyecenter
            print "eye_autotune: bitslipping %d time%s" % ( bitslip_count, ("" if bitslip_count == 1 else "s"))
        for i in xrange(bitslip_count):
            self.bitslip(channel, bit)
        return bitslip_count
    
    def eye_scan(self, channel, bit, verbose=1):
        val = bf(self.read(self.map['DPTRAINING']))
        val[22:20] = channel
        val[19:16] = bit
        val[28] = 1
        val[29] = 0
        self.write(self.map['DPTRAINING'], int(val))
        old_train = 0
        stable_count = 0
        eye_start = 0
        eye_stop = 0
        found_eye_start = 0
        looking_for_stop = 0
        train_in_eye = 0
        for i in xrange(32):
            self.delay(channel, bit, i)
            new_train = self.train_read(channel, bit)
            if i==0:
                old_train = new_train
            else:
                if new_train == old_train:
                    stable_count = stable_count + 1
                    if stable_count > 9:
                        if found_eye_start == 0:
                            eye_start = i-stable_count
                            found_eye_start = 1
                            train_in_eye = new_train
                else:
                    stable_count = 0
                    if found_eye_start == 1:
                        eye_stop = i
                        break
                old_train = new_train
        if verbose == 1:
            print "Ch%2.2d Bit %2.2d Eye scan: (%2.2d - %2.2d) [%2.2X]" % (channel, bit, eye_start, eye_stop, train_in_eye)
        return (eye_start, eye_stop, train_in_eye)		

    '''
    #Thi was the old scaler read function, 
	#updated function below, but lacking num_tirals and wait functionallity	
    def scaler_read(self,channel,sample,num_trials=1,wait=100):
        val = 0
        for trail_i in range(num_trials):
            v = self.train_read(channel, sample, sample_view=1)
            for i in range(wait):
                val_temp = bf(self.read(self.map['DPSCALER']))
                if(val_temp[16]):
                    val += int(val_temp[15:0])
                    break
                
        val /=(1023.0*num_trials)
        return val#[15:0]
    '''
    def scaler_read(self, channel, sample, dontreset=False):
        val = bf(self.read(self.map['DPTRAINING']))
        # this part is complicated
        bfsamp = bf(sample)
        if val[6:4] == channel and val[3:1] == bfsamp[4:2] and not dontreset:
            # we already had these settings, reset it
            val[8] = 1
            val[0] = bfsamp[1]
        else:
            val[6:4] = channel
            val[3:0] = bfsamp[4:1]
			
        self.write(self.map['DPTRAINING'], int(val))
        val = bf(self.read(self.map['DPTRAINING']))
        while not val[8]:
            val = bf(self.read(self.map['DPTRAINING']))
            
        rdval = bf(self.read(self.map['DPSCALER']))
        if bfsamp[0]:
            return rdval[11:0]
        else:
            return rdval[27:16]
			
	#Needs to be tested
    def scaler_read_all(self,channel,num_trials=1,wait=100):
        value_array = [0]*32
        value_array_temp = [0]*32
        for trial_i in range(num_trials):
            for sample_i in range(32):
                value_array_temp[sample_i] = self.scaler_read(channel,sample_i, True)
                value_array[sample_i] += value_array_temp[sample_i]
		value_array /= (1024.0*num_trials)
        return value_array

    '''
    #Old version of eye_autotune    
    # I should believe in exceptions, really I should.
    def eye_autotune(self, channel, bit, verbose=1):
        eyevars = self.eye_scan(channel, bit, verbose)
        if eyevars[0] == 0:
            print "'CA' Eye start not found, checking next eye"
            VCDL_delay = (eyevars[1]/2)
            if (channel <= 2 ):
			    RITC = 0
            if (channel > 2):
		        RITC = 1
            self.delay_VCDL(RITC,int(VCDL_delay))
            eyevars = self.eye_scan(channel,bit,verbose)
            if eyevars[2] != 0x2B and eyevars[2] != 0x95 and eyevars[2] != 0xCA and eyevars[2] != 0x65 and eyevars[2] != 0xB2 and eyevars[2] != 0x59:
                print "eye_autotune error: unknown value in eye (%2.2x %2.2x %2.2x)" % eyevars
                return -1
            eyecenter = 2*VCDL_delay - (eyevars[1] - eyevars[0])/2
            self.delay(channel, bit, int(eyecenter))
            self.delay_VCDL(RITC,0)
            eyevars = self.eye_scan(channel, bit, verbose)
        elif eyevars[2] != 0x2B and eyevars[2] != 0x95 and eyevars[2] != 0xCA and eyevars[2] != 0x65 and eyevars[2] != 0xB2 and eyevars[2] != 0x59:
            print "eye_autotune error: unknown value in eye (%2.2x %2.2x %2.2x)" % eyevars
            return -1
        else:
            eyecenter = (eyevars[1] + eyevars[0])/2
            self.delay(channel, bit, int(eyecenter))
        bitslip_count = 0
        if eyevars[2] == 0x2B or eyevars[2] == 0xB2:
            bitslip_count = 2
        elif eyevars[2] == 0x65 or eyevars[2] == 0x59:
            bitslip_count = 1
        elif eyevars[2] == 0x95:
            bitslip_count = 3
        if verbose == 1:
            print "eye_autotune: setting to delay %d" % eyecenter
            print "eye_autotune: bitslipping %d time%s" % ( bitslip_count, ("" if bitslip_count == 1 else "s"))
        for i in xrange(bitslip_count):
            self.bitslip(channel, bit)
        return bitslip_count
    '''
    
    def delay(self, channel, bit, value):
        val = bf(0)
        val[7:0] = value
        val[19:16] = bit
        val[22:20] = channel
        val[31] = 1
        self.write(self.map['DPIDELAY'], int(val))
        val = bf(self.read(self.map['DPIDELAY']))
        while val[15]:
            val = bf(self.read(self.map['DPIDELAY']))
	    
    def bitslip(self, channel, bit):
        val = bf(self.read(self.map['DPTRAINING']))
        val[22:20] = channel
        val[19:16] = bit
        val[30] = 1
        self.write(self.map['DPTRAINING'], int(val))
        val = bf(self.read(self.map['DPIDELAY']))
        while val[15]:
            val = bf(self.read(self.map['DPIDELAY']))
        
    def rdac(self, ritc, channel, value = None):
        if ritc > 1:
            print "Illegal RITC channel %d" % ritc
            return None
        if channel > 32:
            print "Illegal RITC DAC channel %d" % channel
            return None
        if value is None:
            print "RITC DAC readback not supported yet"
            return None
        else:
            val = bf(0x0)
            val[11:0] = value
            val[17:12] = channel
            val[18] = ritc
            self.write(self.map['RDINPUT'], int(val))
            self.write(self.map['RDCTRL'], 0x1)
            val = bf(self.read(self.map['RDCTRL']))
            while val[1]:
                #print "Loader busy, waiting..."
                val = bf(self.read(self.map['RDCTRL']))
    
    def identify(self):
        ident = bf(self.read(self.map['ident']))
        ver = bf(self.read(self.map['ver']))
        serno = bf(0)
        self.write(self.map['SERIAL'], 0x80000000)
        self.write(self.map['SERIAL'], 0x00000000)
        for i in xrange(57):
            serno[56-i] = self.read(self.map['SERIAL'])
          
        print "Identification Register: %x (%c%c%c%c)" % (int(ident),ident[31:24],ident[23:16],ident[15:8],ident[7:0])
        print "Version Register: %d.%d.%d compiled %d/%d boardrev %d" % (ver[15:12], ver[11:8], ver[7:0], ver[27:24], ver[23:16], ver[31:28] + 1)
        print "Serial Number: %15.15x" % int(serno)

    def read(self, addr):
        return self.dev.read(addr + self.base)
    
    def write(self, addr, value):
        self.dev.write(addr + self.base, value)

    def dac(self, channel, value = None):
        if channel > 8:
            print "Illegal DAC channel (%d)" % channel
            return None
        if value is None:
            return self.read(self.map['settings_dac'] + channel*4)
        else:
            value = value & 0xFFF
            if value > 2000:
                print "DAC value is too high (%d)!" % value
                return None
            elif value < 0:
				print "DAC value is too low (%d)!" % value
				return None
            print "Writing %8.8x to DAC %d" % ( value, channel)
            self.write(self.map['settings_dac'] + channel*4, value)
            return value

    def dac_mv(self, channel, value = None):
        if channel > 8:
            print "Illegal DAC channel (%d)" % channel
            return None
        if value is None:
            return int(self.read(self.map['settings_dac']+channel*4)*2500/4095)
        else:
            value = int(value*4095./2500.) & 0xFFF
            print "Writing %8.8x to DAC %d" % (value, channel)
            self.write(self.map['settings_dac'] + channel*4, value)
            return int(value*4095./2500.)
            
    def atten(self, channel, value = None):
        if value is None:
            return self.read(self.map['settings_atten'] + channel*4)
        else:
            value = value & 0x1F
            self.write(self.map['settings_atten'] + channel*4, value)
            return value
            
    def reset_all_thresholds(self,RITC,reset_value=4095,wait_time=0.01):
        # Reset all thresholds to the highest value
        for i in range(21):
            time.sleep(0.01)
            self.rdac(RITC,i,reset_value)
            
    def read_all_samples(self, channel,wait_time=0.01):
	    sample_values = np.zeros(32)	    
	    for sample_i in range(0,32):
		    sample_values[sample_i]=self.train_read(channel, sample_i, 1)
	    return sample_values
	    
    def read_all_samples_n(self,channel,num_trials):
	    sample_values = [0]*32
	    for sample_i in range(0,32):
		    for n in range(num_trials):
			    sample_values[sample_i]+=float(self.train_read(channel, sample_i, 1))
	    return sample_values
	    
    def read_sample_n(self, channel,sample_number,num_trials):
	    sample_value = 0.0
	    for n in range(num_trials):
		    sample_value+=float(self.train_read(channel, sample_number, 1))
	    sample_value /=float(num_trials)
	    return sample_value

    def autotrain_all_from_mem(self):
        for i in xrange(6):
            self.autotrain_from_mem(i, 0)

    def autotrain_from_mem(self, channel, verbose=1):
        # upper RITCs get mapped to delay channels 4, 5, 6
        if channel > 2:
            delaych = channel + 1
        else:
            delaych = channel
        # step 1, reset the storage system and disable all
        # triggers except soft trigger.
        self.write(self.map['STORCTL'], 0x08)
        # Now literally cycle through all of the IDELAY taps for
        # these inputs.
        full_train = [None]*32
        for i in xrange(32):
            # broadcast delay update
            self.delay(delaych, 13, i)
            # now fetch the full training pattern for this channel
            full_train[i] = self.train_read_from_mem(channel)
        # OK, now we actually have a *full* training pattern
        # matrix: all 12 input lines, with all 32 IDELAY taps.
        # We need to search through those IDELAY taps to locate the eye center.
        for i in xrange(12):
            old_train = 0
            stable_count = 0
            eye_start = 0
            eye_stop = 0
            found_eye_start = 0
            looking_for_stop = 0
            train_in_eye = 0            
            middle_of_eye = 0
            for j in xrange(32):
                new_train = int(full_train[j][i])
                if j==0:
                    old_train = new_train
                else:
                    if new_train == old_train:
                        stable_count = stable_count + 1
                        if stable_count > 9:
                            if found_eye_start == 0:
                                eye_start = j-stable_count
                                found_eye_start = 1
                                train_in_eye = new_train
                    else:
                        stable_count = 0
                        if found_eye_start == 1:
                            eye_stop = j
                            break
                old_train = new_train
            middle_of_eye = eye_start + (eye_stop - eye_start)/2
            if verbose == 1:
                print "Ch%2.2d Bit %2.2d Eye scan: (%2.2d - %2.2d) [%2.2X]" % (channel, i, eye_start, eye_stop, train_in_eye)                
                print "Ch%2.2d Bit %2.2d Setting delay to %d" % (channel, i, middle_of_eye)
            self.delay(delaych, i, middle_of_eye)
        return
                
    def train_read_from_mem(self, channel):
        # trigger
        self.write(self.map['STORCTL'], 0x02)
        val = bf(self.read(self.map['STORCTL']))
        # read
        while not val[0]:
            val = bf(self.read(self.map['STORCTL']))
    
        # update the read pointer
        self.write(self.map['SAMPDATA']+0x200*channel*4, 0)
        # now I can read from that address
        a0 = bf(self.read(self.map['SAMPDATA']+0x200*channel*4))
        a1 = bf(self.read(self.map['SAMPDATA']+0x200*channel*4))
        a2 = bf(self.read(self.map['SAMPDATA']+0x200*channel*4))
        a3 = bf(self.read(self.map['SAMPDATA']+0x200*channel*4))
        # clear
        self.write(self.map['STORCTL'], 0x04)
        
        train = [None]*12
        for i in xrange(12):
            train_tmp = bf(0)
            train_tmp[0] = a0[0+i]
            train_tmp[1] = a0[12+i]
            train_tmp[2] = a1[0+i]
            train_tmp[3] = a1[12+i]
            train_tmp[4] = a2[0+i]
            train_tmp[5] = a2[12+i]
            train_tmp[6] = a3[0+i]
            train_tmp[7] = a3[12+i]
            train[i] = train_tmp
        
        return train
        
    
    # Initialize the interconnect between this GLITC and its
    # upstream partner.
    # What this does:
    # Reset ISERDES[up] for me and ISERDES[down] for gup
    # Place OSERDES[up] for me and OSERDES[down] for gup in training mode, and
    #   disable input training complete.
    # Reset OSERDES[up] for me and OSERDES[down] for gup
    # Clock enable OSERDES[up] for me and OSERDES[down] for gup
    # Set bitslips/nominal delays for these paths (up for me, down for gup)
    #
    # Then:
    # *) Read GITRAINDOWN for gup. If it's not EB7ED, then issue realign for
    #    gup (write 0x10 to 'control'). Reread. If it's now not EB7ED, throw an error.
    # *) Read GITRAINUP for me. If it's not EB7ED, throw an error.
    # *) Set input training done[up] for me, and input training done[down] for gup
    # *) Send sync[up] for me.
    # *) Send echo[up] for me, and check latency.
    # *) Send echo[down] for gup, and check latency.
    #
    # Note that OFFBOARD initialization is done via a different function.
    def onboard_intercom_initialize(self, gup):
        myctl0 = bf(self.read(self.map['GICTRL0']))
        upctl0 = bf(gup.read(gup.map['GICTRL0']))
        myctl1 = bf(self.read(self.map['GICTRL1']))
        upctl1 = bf(gup.read(gup.map['GICTRL1']))

        # Put everything into a known state.
        # Disable input buffer.
        # Disable clock enable.
        # Disable correlation enable.
        # Training mode off.
        # Training mode incomplete.
        # Reset status.
        myctl0[15:0] = 0x4
        myctl1[15:0] = 0x1000
        upctl0[31:16] = 0x4
        upctl1[31:16] = 0x1000
        self.write(self.map['GICTRL0'], int(myctl0))
        self.write(self.map['GICTRL1'], int(myctl1))
        gup.write(gup.map['GICTRL0'], int(upctl0))
        gup.write(gup.map['GICTRL1'], int(upctl1))

        print "GICTRL0 at reset: %8.8x" % self.read(self.map['GICTRL0'])
        print "GICTRL0 on UP GLITC at reset: %8.8x" % gup.read(gup.map['GICTRL0'])
        
        # Reset ISERDES up for me, enable input buffer
        myctl0[15:0] = 0x0001
        # Reset ISERDES down for gup, enable input buffer
        upctl0[31:16] = 0x0001
        self.write(self.map['GICTRL0'], int(myctl0))
        gup.write(gup.map['GICTRL0'], int(upctl0))
        
        # Put my OSERDES up into training mode
        myctl1[15:0] = 0x0004
        # Put gup OSERDES down into training mode
        upctl1[31:16] = 0x0004        
        self.write(self.map['GICTRL1'], int(myctl1))
        gup.write(gup.map['GICTRL1'], int(upctl1))

        # Reset OSERDES up for me.
        myctl0[15:0] = 0x0002
        # and reset OSERDES down for gup
        upctl0[31:16] = 0x0002
        self.write(self.map['GICTRL0'], int(myctl0))
        gup.write(gup.map['GICTRL0'], int(upctl0))

        # Now clock enable OSERDES up for me
        myctl0[15:0] = 0x0008
        # and down for gup
        upctl0[31:16] = 0x0008
        self.write(self.map['GICTRL0'], int(myctl0))
        gup.write(gup.map['GICTRL0'], int(upctl0))

        print "After reset: GICTRL0 %8.8x, GICTRL1 %8.8x" % (self.read(self.map['GICTRL0']), self.read(self.map['GICTRL1']))
        print "UP after reset: GICTRL0 %8.8x, GICTRL1 %8.8x" % (gup.read(gup.map['GICTRL0']), gup.read(gup.map['GICTRL1']))
        
        # Now bitslip each of my 'up' ISERDESes 3 times.
        # And bitslip each of gup's 'down' iserdeses 3 times
        # set to nominal values
        
        # Note that you probably need a small delay after
        # each 'delay' or bitslip write. Here printing the readback of the trains
        # basically accomplishes that.        
        for bit in xrange(5):
            self.delay(3, bit, 24)
            gup.delay(7, bit, 24)
        print "GITRAINUP after idelay set: %8.8x" % self.read(self.map['GITRAINUP'])
        print "UPs GITRAINDOWN after idelay set: %8.8x" % gup.read(gup.map['GITRAINDOWN'])
        for i in xrange(3):
            self.bitslip(3, 0)
            self.bitslip(3, 1)
            self.bitslip(3, 2)
            self.bitslip(3, 3)
            self.bitslip(3, 4)
            gup.bitslip(7, 0)
            gup.bitslip(7, 1)
            gup.bitslip(7, 2)
            gup.bitslip(7, 3)
            gup.bitslip(7, 4)
            print "GITRAINUP after bitslip: %8.8x" % self.read(self.map['GITRAINUP'])
            print "UPs GITRAINDOWN after bitslip: %8.8x" % gup.read(gup.map['GITRAINDOWN'])
        
        # Now read the training pattern on gup's TRAINDOWN
        train = bf(gup.read(gup.map['GITRAINDOWN']))
        if (train[19:0] != 0xEB7ED):
            print "UP path GLITC is out of alignment (%5.5x). Realigning." % train[19:0]
            # Issue a clock shift.
            gup.write(gup.map['CONTROL'], 0x10)
            time.sleep(0.001)
            train = bf(gup.read(gup.map['GITRAINDOWN']))
            if (train[19:0] != 0xEB7ED):
                print "UP path GLITC is still out of alignment! Initialization failed."
                return
            else:
                print "UP path GLITC is now clock-aligned."

        # Set input training done and disable output training mode.
        myctl1[15:0] = 0x2
        upctl1[31:16] = 0x2
        self.write(self.map['GICTRL1'], int(myctl1))
        gup.write(gup.map['GICTRL1'], int(upctl1))
        ctl = bf(gup.read(gup.map['GICTRL1']))
        print "UP path GICTRL1 before sync: %4.4x" % ctl[31:16]
        # Send SYNC.
        myctl1[3] = 1
        self.write(self.map['GICTRL1'], int(myctl1))
        ctl = bf(gup.read(gup.map['GICTRL1']))
        print "UP path GICTRL1 after sync: %4.4x" % ctl[31:16]
        # Now send an echo to up.
        myctl1[15:0] = 0x42
        self.write(self.map['GICTRL1'], int(myctl1))
        ctl = bf(self.read(self.map['GICTRL1']))
        toUpLatency = ctl[11:8]
        print "Latency to UP echo response: %d" % toUpLatency
        print "Base latency: %d" % ctl[15:12]
        # Now send an echo from up
        upctl1[31:16] = 0x42
        gup.write(gup.map['GICTRL1'], int(upctl1))
        ctl = bf(gup.read(gup.map['GICTRL1']))
        fromUpLatency = ctl[27:24]
        print "Latency from UP echo response: %d" % fromUpLatency
        if toUpLatency != fromUpLatency:
            print "Echo latencies don't match! Problem with intercom initialization."
            return
        print "On-board intercom initialized."
        
    def soft_trigger(self):
        val = bf(self.read(self.map['STORCTL']))
        val[1] = 1
        self.write(self.map['STORCTL'], int(val))
        
        
    def trigger_read(self,timeout=1000):
        val = bf(self.read(self.map['STORCTL']))
        count = 0
        while not val[0]:
            val = bf(self.read(self.map['STORCTL']))
            count = count + 1
            if timeout and count > timeout:
                print "Timeout waiting for STORCTL data ready"
                return None
            
        # now trigger is ready
        # prep data
        data = [None]*3072
        for i in xrange(3072):
            data[i] = self.read(self.map['SAMPDATA'])
        
        # now clear trigger
        val[2] = 1
        self.write(self.map['STORCTL'], int(val))
        return data
            
        
'''		
class SPI:
    map = { 'SPCR'       : 0x000000,
            'SPSR'       : 0x000004,
            'SPDR'       : 0x000008,
            'SPER'       : 0x00000C }
    
    cmd = { 'RES'        : 0xAB ,
            'RDID'       : 0x9F ,
            'WREN'       : 0x06 ,
            'WRDI'       : 0x04 ,
            'RDSR'       : 0x05 ,
            'WRSR'       : 0x01 ,
            'READ'       : 0x03 ,
            'FASTREAD'   : 0x0B ,
            'PP'         : 0x02 ,
            'SE'         : 0xD8 ,
            'BE'         : 0xC7 }
    
    bits = { 'SPIF'      : 0x80,
             'WCOL'      : 0x40,
             'WFFULL'    : 0x08,
             'WFEMPTY'   : 0x04,
             'RFFULL'    : 0x02,
             'RFEMPTY'   : 0x01 }
    
    def __init__(self, dev, base):
        self.dev = dev
        self.base = base
        val = bf(self.dev.read(self.base + self.map['SPCR']))
        val[6] = 1;
        val[3] = 0;
        val[2] = 0;
        self.dev.write(self.base + self.map['SPCR'], int(val))

    def command(self, device, command, dummy_bytes, num_read_bytes, data_in = [] ):
        self.dev.spi_cs(device, 1)
        self.dev.write(self.base + self.map['SPDR'], command)
        for dat in data_in:
            self.dev.write(self.base + self.map['SPDR'], dat)
        for i in range(dummy_bytes):
            self.dev.write(self.base + self.map['SPDR'], 0x00)
        # Empty the read FIFO.
        while not (self.dev.read(self.base + self.map['SPSR']) & self.bits['RFEMPTY']):
            self.dev.read(self.base + self.map['SPDR'])
        rdata = []
        for i in range(num_read_bytes):
            self.dev.write(self.base + self.map['SPDR'], 0x00)
            rdata.append(self.dev.read(self.base + self.map['SPDR']))
        self.dev.spi_cs(device, 0)    
        return rdata
    
    def identify(self, device=0):
        res = self.command(device, self.cmd['RES'], 3, 1)
        print "Electronic Signature: 0x%x" % res[0]
        res = self.command(device, self.cmd['RDID'], 0, 3)
        print "Manufacturer ID: 0x%x" % res[0]
        print "Device ID: 0x%x 0x%x" % (res[1], res[2])

    def read(self, address, length=1, device=0):
        data_in = []
        data_in.append((address >> 16) & 0xFF)
        data_in.append((address >> 8) & 0xFF)
        data_in.append(address & 0xFF)
        res = self.command(device, self.cmd['READ'], 0, length, data_in)
        return res        
'''
        
class TISC(ocpci.Device):
    map = { 'ident'      : 0x000000,
            'ver'        : 0x000004,
            'clock'      : 0x000008,
            'spi_cs'     : 0x00000C,
            'spi_base'   : 0x000010,
            'glitc_ctrl' : 0x000040,
            'GA'         : 0x100000,
            'GB'         : 0x140000,
            'GC'         : 0x180000,
            'GD'         : 0x1C0000 }

    glitc_base           = 0x100000
    glitc_offset         = 0x040000

    glitc_init_bit         = 0x100
    glitc_prog_bit         = 0x1
    glitc_done_bit         =  0x10000
    glitc_config_done_bit  = 0x10

    def __init__(self, path="/sys/class/uio/uio0"):
        ocpci.Device.__init__(self, path, 2*1024*1024)
        self.spi = spi.SPI(self, self.map['spi_base'])
        self.GA = GLITC(self, self.map['GA'])
        self.GB = GLITC(self, self.map['GB'])
        self.GC = GLITC(self, self.map['GC'])
        self.GD = GLITC(self, self.map['GD'])

    def __repr__(self):
        return "<TISC at %s>" % self.path

    def __str__(self):
        return "TISC (@%s)" % self.path
    
    def spi_cs(self, device, state):
        # We only have 1 SPI device.
        val = bf(self.read(self.map['spi_cs']))
        val[device] = state
        self.write(self.map['spi_cs'], int(val))

    def status(self):
        gc = bf(self.read(self.map['glitc_ctrl']))
        for i in xrange(4):
            print "GLITC %c Status: INIT_B %s" % ( chr(ord('A')+i), "went high" if gc[8+i] else "did not go high")
            print "              : DONE %s" % ( "went high" if gc[16+i] else "did not go high")
            print "              : %s" % ( "is in normal mode" if gc[4+i] else "is in config mode")
            print ""
        clock = bf(self.read(self.map['clock']))
        print "Clock Status: Local Clock is %s (EN_LOCAL_CLK = %d)" % ("enabled" if clock[1] else "not enabled", clock[1])
        print "            :   SYS Clock is %s (SYSCLK_SEL = %d)" % ("Local Clock" if clock[0] else "TURF Clock", clock[0])

        
    def identify(self):
        ident = bf(self.read(self.map['ident']))
        ver = bf(self.read(self.map['ver']))
        print "Identification Register: %x (%c%c%c%c)" % (int(ident),ident[31:24],ident[23:16],ident[15:8],ident[7:0])
        print "Version Register: %d.%d.%d compiled %d/%d" % (ver[15:12], ver[11:8], ver[7:0], ver[28:24], ver[23:16])

    def glitcs(self):
        return [self.GA, self.GB, self.GC, self.GD]
        
    def gprogram(self, glitc, path):
        if glitc > 3 or glitc < 0:
            return
        with open(path,"rb") as f:
            header = "\x00\x09\x0F\xF0\x0F\xF0\x0F\xF0\x0F\xF0\x00"
            # First 11 bytes: header
            test = f.read(11)
            if header != test:
                print "Improper header in file %s." % path
                return
            version = struct.unpack(">H", f.read(2))[0]
            if version != 1:
                print "Improper file version: %d." % version
                return
            for x in xrange(4):
                tag = f.read(1)
                length = struct.unpack(">H", f.read(2))[0]
                string = f.read(length)
                if tag == 'a':
                    print "Filename: %s" % string
                elif tag == 'b':
                    print "Device name: %s" % string
                elif tag == 'c':
                    print "Date stamp: %s" % string
                elif tag == 'd':
                    print "Time stamp: %s" % string
                else:
                    print "Improper tag: %c" % tag
                    return
            btag = f.read(1)
            if btag != 'e':
                print "Improper bulk tag: %c" % btag
            length = struct.unpack(">I", f.read(4))[0]
            print "Bitstream length: %d" % length
            print "Issuing program request."
            tmp = self.read(self.map['glitc_ctrl'])
            tmp = tmp | (self.glitc_prog_bit<<glitc)
            self.write(self.map['glitc_ctrl'], tmp)
            for i in xrange(1000):
                if self.read(self.map['glitc_ctrl']) & (self.glitc_init_bit<<glitc):
                    break
            if i == 1000:
                print "INIT_B did not go high - program failed."
                return
            print "Initialization complete, INIT_B is high."
            i = 0
            next_check = 0
            while i < length:
                val = struct.unpack("<I", f.read(4))[0]
                val = ((val>>1) & 0x55555555L) | ((val & 0x55555555L) << 1)
                val = ((val>>2) & 0x33333333L) | ((val & 0x33333333L) << 2)
                val = ((val>>4) & 0x0F0F0F0FL) | ((val & 0x0F0F0F0FL) << 4)
                val = ((val>>8) & 0x00FF00FFL) | ((val & 0x00FF00FFL) << 8)
                val = ((val >> 16) & 0x0000FFFFL) | ((val & 0x0000FFFFL) << 16)
                self.write(self.glitc_base + self.glitc_offset*glitc, val)
                if i == next_check:
                    print "%d / %d" % (i , length)
                    next_check = next_check + (length/4)
                    next_check = next_check & ~0x3
                i = i + 4
            print "Bitstream load done - checking DONE bit."
            if not self.read(self.map['glitc_ctrl']) & (self.glitc_done_bit << glitc):
                print "Programming failed - DONE bit not high (%8.8x)" % self.read(self.map['glitc_ctrl'])
            else:
                tmp = self.read(self.map['glitc_ctrl'])
                tmp = tmp | (self.glitc_config_done_bit << glitc)
                self.write(self.map['glitc_ctrl'], tmp)
                print "Programming complete."
