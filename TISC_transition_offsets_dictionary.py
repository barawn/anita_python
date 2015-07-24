
def get_offsets(TISC_n,GLITC_n,channel,RITC_DAC_Number):
	offset_dict = {}

	# Syntax (TISC_Number,GLITC_Number,Channel_Number,RITC_DAC_Number,Transition_Point) = offset

	#Note, a note was made for any offset with a |delta| > 1.75
	#Delta is a measure of how many dac counts off you are based on the difference on the 
	#slope before and after the transition. 


	#---------------------------------------
	#---------------GLITC 0-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 0
	# Channel 0
	offset_dict[(10002,0,0,0,2048)]=54
	offset_dict[(10002,0,0,0,1024)]=47
	offset_dict[(10002,0,0,0,512)] =18
	offset_dict[(10002,0,0,0,256)] = 5
	offset_dict[(10002,0,0,0,128)] = 0

	offset_dict[(10002,0,0,1,2048)]=55
	offset_dict[(10002,0,0,1,1024)]=21
	offset_dict[(10002,0,0,1,512)] =10
	offset_dict[(10002,0,0,1,256)] = 6
	offset_dict[(10002,0,0,1,128)] = 0

	offset_dict[(10002,0,0,2,2048)]=42
	offset_dict[(10002,0,0,2,1024)]=57 
	offset_dict[(10002,0,0,2,512)] =17
	offset_dict[(10002,0,0,2,256)] = 7
	offset_dict[(10002,0,0,2,128)] = 0

	offset_dict[(10002,0,0,3,2048)]=85
	offset_dict[(10002,0,0,3,1024)]=23
	offset_dict[(10002,0,0,3,512)] =16
	offset_dict[(10002,0,0,3,256)] = 4
	offset_dict[(10002,0,0,3,128)] = 0

	offset_dict[(10002,0,0,4,2048)]=79 
	offset_dict[(10002,0,0,4,1024)]=25
	offset_dict[(10002,0,0,4,512)] =16
	offset_dict[(10002,0,0,4,256)] = 4
	offset_dict[(10002,0,0,4,128)] = 0

	offset_dict[(10002,0,0,5,2048)]= 1 
	offset_dict[(10002,0,0,5,1024)]=41
	offset_dict[(10002,0,0,5,512)] = 8
	offset_dict[(10002,0,0,5,256)] = 4
	offset_dict[(10002,0,0,5,128)] = 0

	offset_dict[(10002,0,0,6,2048)]=86
	offset_dict[(10002,0,0,6,1024)]=24
	offset_dict[(10002,0,0,6,512)] =15
	offset_dict[(10002,0,0,6,256)] = 4
	offset_dict[(10002,0,0,6,128)] = 0

	# TISC 10002
	# GLITC 0
	# Channel 1
	offset_dict[(10002,0,1,7,2048)]=48 
	offset_dict[(10002,0,1,7,1024)]=36
	offset_dict[(10002,0,1,7,512)] =17 
	offset_dict[(10002,0,1,7,256)] = 10
	offset_dict[(10002,0,1,7,128)] = 0

	offset_dict[(10002,0,1,8,2048)]=43
	offset_dict[(10002,0,1,8,1024)]=27 
	offset_dict[(10002,0,1,8,512)] =4
	offset_dict[(10002,0,1,8,256)] = 7
	offset_dict[(10002,0,1,8,128)] = 0

	offset_dict[(10002,0,1,9,2048)]=43
	offset_dict[(10002,0,1,9,1024)]=21 
	offset_dict[(10002,0,1,9,512)] =12
	offset_dict[(10002,0,1,9,256)] = 5
	offset_dict[(10002,0,1,9,128)] = 0

	offset_dict[(10002,0,1,10,2048)]=71 
	offset_dict[(10002,0,1,10,1024)]=27
	offset_dict[(10002,0,1,10,512)] =12 
	offset_dict[(10002,0,1,10,256)] = 8
	offset_dict[(10002,0,1,10,128)] = 0

	offset_dict[(10002,0,1,11,2048)]=43
	offset_dict[(10002,0,1,11,1024)]=16
	offset_dict[(10002,0,1,11,512)] = 7
	offset_dict[(10002,0,1,11,256)] = 8
	offset_dict[(10002,0,1,11,128)] = 0

	offset_dict[(10002,0,1,12,2048)]=39
	offset_dict[(10002,0,1,12,1024)]=19
	offset_dict[(10002,0,1,12,512)] = 9
	offset_dict[(10002,0,1,12,256)] = 6
	offset_dict[(10002,0,1,12,128)] = 0

	offset_dict[(10002,0,1,13,2048)]=35
	offset_dict[(10002,0,1,13,1024)]=13
	offset_dict[(10002,0,1,13,512)] =17
	offset_dict[(10002,0,1,13,256)] = 7
	offset_dict[(10002,0,1,13,128)] = 0

	# TISC 10002
	# GLITC 0
	# Channel 2
	offset_dict[(10002,0,2,14,2048)]=34
	offset_dict[(10002,0,2,14,1024)]=32 
	offset_dict[(10002,0,2,14,512)] = 4 
	offset_dict[(10002,0,2,14,256)] = 7
	offset_dict[(10002,0,2,14,128)] = 0

	offset_dict[(10002,0,2,15,2048)]=58
	offset_dict[(10002,0,2,15,1024)]=32 
	offset_dict[(10002,0,2,15,512)] =18
	offset_dict[(10002,0,2,15,256)] = 6
	offset_dict[(10002,0,2,15,128)] = 0

	offset_dict[(10002,0,2,16,2048)]=71
	offset_dict[(10002,0,2,16,1024)]=34
	offset_dict[(10002,0,2,16,512)] = 9
	offset_dict[(10002,0,2,16,256)] = 5
	offset_dict[(10002,0,2,16,128)] = 0

	offset_dict[(10002,0,2,17,2048)]=65
	offset_dict[(10002,0,2,17,1024)]=32
	offset_dict[(10002,0,2,17,512)] = 7 
	offset_dict[(10002,0,2,17,256)] = 0
	offset_dict[(10002,0,2,17,128)] = 0

	offset_dict[(10002,0,2,18,2048)]=68
	offset_dict[(10002,0,2,18,1024)]= 8 
	offset_dict[(10002,0,2,18,512)] =14
	offset_dict[(10002,0,2,18,256)] = 6
	offset_dict[(10002,0,2,18,128)] = 0

	offset_dict[(10002,0,2,19,2048)]=66
	offset_dict[(10002,0,2,19,1024)]=22
	offset_dict[(10002,0,2,19,512)] =13
	offset_dict[(10002,0,2,19,256)] = 6
	offset_dict[(10002,0,2,19,128)] = 0

	offset_dict[(10002,0,2,20,2048)]=51 
	offset_dict[(10002,0,2,20,1024)]=28 
	offset_dict[(10002,0,2,20,512)] =13
	offset_dict[(10002,0,2,20,256)] = 9
	offset_dict[(10002,0,2,20,128)] = 0

	# TISC 10002
	# GLITC 0
	# Channel 4
	offset_dict[(10002,0,4,0,2048)]=67
	offset_dict[(10002,0,4,0,1024)]=36 
	offset_dict[(10002,0,4,0,512)] =13
	offset_dict[(10002,0,4,0,256)] = 3
	offset_dict[(10002,0,4,0,128)] = 0

	offset_dict[(10002,0,4,1,2048)]=68
	offset_dict[(10002,0,4,1,1024)]=33 
	offset_dict[(10002,0,4,1,512)] =22
	offset_dict[(10002,0,4,1,256)] = 8
	offset_dict[(10002,0,4,1,128)] = 0

	offset_dict[(10002,0,4,2,2048)]=73
	offset_dict[(10002,0,4,2,1024)]=14 
	offset_dict[(10002,0,4,2,512)] =17
	offset_dict[(10002,0,4,2,256)] = 7
	offset_dict[(10002,0,4,2,128)] = 0

	offset_dict[(10002,0,4,3,2048)]=54
	offset_dict[(10002,0,4,3,1024)]=29
	offset_dict[(10002,0,4,3,512)] =17
	offset_dict[(10002,0,4,3,256)] = 4
	offset_dict[(10002,0,4,3,128)] = 0

	offset_dict[(10002,0,4,4,2048)]=31
	offset_dict[(10002,0,4,4,1024)]=22
	offset_dict[(10002,0,4,4,512)] =10
	offset_dict[(10002,0,4,4,256)] = 6
	offset_dict[(10002,0,4,4,128)] = 0

	offset_dict[(10002,0,4,5,2048)]=48
	offset_dict[(10002,0,4,5,1024)]=29
	offset_dict[(10002,0,4,5,512)] =13
	offset_dict[(10002,0,4,5,256)] = 7
	offset_dict[(10002,0,4,5,128)] = 0

	offset_dict[(10002,0,4,6,2048)]=34
	offset_dict[(10002,0,4,6,1024)]=28
	offset_dict[(10002,0,4,6,512)] =17
	offset_dict[(10002,0,4,6,256)] = 5
	offset_dict[(10002,0,4,6,128)] = 0

	# TISC 10002
	# GLITC 0
	# Channel 5
	offset_dict[(10002,0,5,7,2048)]=66
	offset_dict[(10002,0,5,7,1024)]=18
	offset_dict[(10002,0,5,7,512)] = 7
	offset_dict[(10002,0,5,7,256)] = 6
	offset_dict[(10002,0,5,7,128)] = 0

	offset_dict[(10002,0,5,8,2048)]=58
	offset_dict[(10002,0,5,8,1024)]=20
	offset_dict[(10002,0,5,8,512)] = 4
	offset_dict[(10002,0,5,8,256)] = 8
	offset_dict[(10002,0,5,8,128)] = 0

	offset_dict[(10002,0,5,9,2048)]=71 
	offset_dict[(10002,0,5,9,1024)]=27
	offset_dict[(10002,0,5,9,512)] =10
	offset_dict[(10002,0,5,9,256)] = 7
	offset_dict[(10002,0,5,9,128)] = 0

	offset_dict[(10002,0,5,10,2048)]=40
	offset_dict[(10002,0,5,10,1024)]=23
	offset_dict[(10002,0,5,10,512)] =16
	offset_dict[(10002,0,5,10,256)] = 8
	offset_dict[(10002,0,5,10,128)] = 0

	offset_dict[(10002,0,5,11,2048)]=13 
	offset_dict[(10002,0,5,11,1024)]=45
	offset_dict[(10002,0,5,11,512)] = 9
	offset_dict[(10002,0,5,11,256)] = 0
	offset_dict[(10002,0,5,11,128)] = 0

	offset_dict[(10002,0,5,12,2048)]=23 
	offset_dict[(10002,0,5,12,1024)]=33
	offset_dict[(10002,0,5,12,512)] =13
	offset_dict[(10002,0,5,12,256)] = 8
	offset_dict[(10002,0,5,12,128)] = 0

	offset_dict[(10002,0,5,13,2048)]=71
	offset_dict[(10002,0,5,13,1024)]=23
	offset_dict[(10002,0,5,13,512)] =17
	offset_dict[(10002,0,5,13,256)] = 8
	offset_dict[(10002,0,5,13,128)] = 0

	# TISC 10002
	# GLITC 0
	# Channel 6
	offset_dict[(10002,0,6,14,2048)]=39
	offset_dict[(10002,0,6,14,1024)]=27
	offset_dict[(10002,0,6,14,512)] =20 
	offset_dict[(10002,0,6,14,256)] = 8
	offset_dict[(10002,0,6,14,128)] = 0

	offset_dict[(10002,0,6,15,2048)]=63
	offset_dict[(10002,0,6,15,1024)]=51
	offset_dict[(10002,0,6,15,512)] =15
	offset_dict[(10002,0,6,15,256)] = 5
	offset_dict[(10002,0,6,15,128)] = 0

	offset_dict[(10002,0,6,16,2048)]=52
	offset_dict[(10002,0,6,16,1024)]=20
	offset_dict[(10002,0,6,16,512)] = 9
	offset_dict[(10002,0,6,16,256)] = 5
	offset_dict[(10002,0,6,16,128)] = 0

	offset_dict[(10002,0,6,17,2048)]=27 
	offset_dict[(10002,0,6,17,1024)]=36
	offset_dict[(10002,0,6,17,512)] =11
	offset_dict[(10002,0,6,17,256)] = 6
	offset_dict[(10002,0,6,17,128)] = 0

	offset_dict[(10002,0,6,18,2048)]=50
	offset_dict[(10002,0,6,18,1024)]=30
	offset_dict[(10002,0,6,18,512)] =12
	offset_dict[(10002,0,6,18,256)] = 2
	offset_dict[(10002,0,6,18,128)] = 0

	offset_dict[(10002,0,6,19,2048)]=56
	offset_dict[(10002,0,6,19,1024)]=31
	offset_dict[(10002,0,6,19,512)] =19
	offset_dict[(10002,0,6,19,256)] = 8
	offset_dict[(10002,0,6,19,128)] = 0

	offset_dict[(10002,0,6,20,2048)]=16 
	offset_dict[(10002,0,6,20,1024)]=37
	offset_dict[(10002,0,6,20,512)] =18
	offset_dict[(10002,0,6,20,256)] = 6
	offset_dict[(10002,0,6,20,128)] = 0


	#---------------------------------------
	#---------------GLITC 1-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 1
	# Channel 0
	offset_dict[(10002,1,0,0,2048)]=59
	offset_dict[(10002,1,0,0,1024)]=45 
	offset_dict[(10002,1,0,0,512)] =12
	offset_dict[(10002,1,0,0,256)] = 5
	offset_dict[(10002,1,0,0,128)] = 0

	offset_dict[(10002,1,0,1,2048)]=37
	offset_dict[(10002,1,0,1,1024)]=23 
	offset_dict[(10002,1,0,1,512)] =20
	offset_dict[(10002,1,0,1,256)] = 7
	offset_dict[(10002,1,0,1,128)] = 0

	offset_dict[(10002,1,0,2,2048)]=76
	offset_dict[(10002,1,0,2,1024)]=42
	offset_dict[(10002,1,0,2,512)] =15
	offset_dict[(10002,1,0,2,256)] = 6
	offset_dict[(10002,1,0,2,128)] = 0

	offset_dict[(10002,1,0,3,2048)]=47
	offset_dict[(10002,1,0,3,1024)]=23
	offset_dict[(10002,1,0,3,512)] =11
	offset_dict[(10002,1,0,3,256)] = 7
	offset_dict[(10002,1,0,3,128)] = 0

	offset_dict[(10002,1,0,4,2048)]=66
	offset_dict[(10002,1,0,4,1024)]=19
	offset_dict[(10002,1,0,4,512)] =19
	offset_dict[(10002,1,0,4,256)] = 4
	offset_dict[(10002,1,0,4,128)] = 0

	offset_dict[(10002,1,0,5,2048)]=34
	offset_dict[(10002,1,0,5,1024)]=44 
	offset_dict[(10002,1,0,5,512)] =14
	offset_dict[(10002,1,0,5,256)] =10
	offset_dict[(10002,1,0,5,128)] = 0

	offset_dict[(10002,1,0,6,2048)]=63
	offset_dict[(10002,1,0,6,1024)]=22
	offset_dict[(10002,1,0,6,512)] =14
	offset_dict[(10002,1,0,6,256)] = 6
	offset_dict[(10002,1,0,6,128)] = 0

	# TISC 10002
	# GLITC 1
	# Channel 1
	offset_dict[(10002,1,1,7,2048)]=34
	offset_dict[(10002,1,1,7,1024)]=30
	offset_dict[(10002,1,1,7,512)] =24
	offset_dict[(10002,1,1,7,256)] = 6
	offset_dict[(10002,1,1,7,128)] = 0

	offset_dict[(10002,1,1,8,2048)]=58
	offset_dict[(10002,1,1,8,1024)]=44
	offset_dict[(10002,1,1,8,512)] =12
	offset_dict[(10002,1,1,8,256)] =11
	offset_dict[(10002,1,1,8,128)] = 0

	offset_dict[(10002,1,1,9,2048)]=75
	offset_dict[(10002,1,1,9,1024)]=33
	offset_dict[(10002,1,1,9,512)] =18
	offset_dict[(10002,1,1,9,256)] = 5
	offset_dict[(10002,1,1,9,128)] = 0

	offset_dict[(10002,1,1,10,2048)]=39
	offset_dict[(10002,1,1,10,1024)]=31
	offset_dict[(10002,1,1,10,512)] =21
	offset_dict[(10002,1,1,10,256)] = 5
	offset_dict[(10002,1,1,10,128)] = 0

	offset_dict[(10002,1,1,11,2048)]=82
	offset_dict[(10002,1,1,11,1024)]=33
	offset_dict[(10002,1,1,11,512)] =18
	offset_dict[(10002,1,1,11,256)] = 5
	offset_dict[(10002,1,1,11,128)] = 0

	offset_dict[(10002,1,1,12,2048)]=47
	offset_dict[(10002,1,1,12,1024)]=32
	offset_dict[(10002,1,1,12,512)] =19
	offset_dict[(10002,1,1,12,256)] = 5
	offset_dict[(10002,1,1,12,128)] = 0

	offset_dict[(10002,1,1,13,2048)]=59
	offset_dict[(10002,1,1,13,1024)]=25
	offset_dict[(10002,1,1,13,512)] =16
	offset_dict[(10002,1,1,13,256)] = 8
	offset_dict[(10002,1,1,13,128)] = 0

	# TISC 10002
	# GLITC 1
	# Channel 2
	offset_dict[(10002,1,2,14,2048)]=78
	offset_dict[(10002,1,2,14,1024)]=31
	offset_dict[(10002,1,2,14,512)] =13
	offset_dict[(10002,1,2,14,256)] = 9
	offset_dict[(10002,1,2,14,128)] = 0

	offset_dict[(10002,1,2,15,2048)]=50
	offset_dict[(10002,1,2,15,1024)]=35
	offset_dict[(10002,1,2,15,512)] =17
	offset_dict[(10002,1,2,15,256)] = 7
	offset_dict[(10002,1,2,15,128)] = 0

	offset_dict[(10002,1,2,16,2048)]=28
	offset_dict[(10002,1,2,16,1024)]=19
	offset_dict[(10002,1,2,16,512)] = 8
	offset_dict[(10002,1,2,16,256)] = 6
	offset_dict[(10002,1,2,16,128)] = 0

	offset_dict[(10002,1,2,17,2048)]=48
	offset_dict[(10002,1,2,17,1024)]=28
	offset_dict[(10002,1,2,17,512)] =13 
	offset_dict[(10002,1,2,17,256)] = 5
	offset_dict[(10002,1,2,17,128)] = 0

	offset_dict[(10002,1,2,18,2048)]=41
	offset_dict[(10002,1,2,18,1024)]=17 
	offset_dict[(10002,1,2,18,512)] =29
	offset_dict[(10002,1,2,18,256)] = 7
	offset_dict[(10002,1,2,18,128)] = 0

	offset_dict[(10002,1,2,19,2048)]=62 
	offset_dict[(10002,1,2,19,1024)]=29
	offset_dict[(10002,1,2,19,512)] =16
	offset_dict[(10002,1,2,19,256)] = 8
	offset_dict[(10002,1,2,19,128)] = 0

	offset_dict[(10002,1,2,20,2048)]=41
	offset_dict[(10002,1,2,20,1024)]=39 
	offset_dict[(10002,1,2,20,512)] =15
	offset_dict[(10002,1,2,20,256)] = 5
	offset_dict[(10002,1,2,20,128)] = 0

	# TISC 10002
	# GLITC 1
	# Channel 4
	offset_dict[(10002,1,4,0,2048)]=65 
	offset_dict[(10002,1,4,0,1024)]=33
	offset_dict[(10002,1,4,0,512)] = 4
	offset_dict[(10002,1,4,0,256)] =11
	offset_dict[(10002,1,4,0,128)] = 0

	offset_dict[(10002,1,4,1,2048)]=78
	offset_dict[(10002,1,4,1,1024)]=37 
	offset_dict[(10002,1,4,1,512)] =11
	offset_dict[(10002,1,4,1,256)] = 7
	offset_dict[(10002,1,4,1,128)] = 0

	offset_dict[(10002,1,4,2,2048)]=100
	offset_dict[(10002,1,4,2,1024)]=16 
	offset_dict[(10002,1,4,2,512)] =21
	offset_dict[(10002,1,4,2,256)] = 5
	offset_dict[(10002,1,4,2,128)] = 0

	offset_dict[(10002,1,4,3,2048)]=85
	offset_dict[(10002,1,4,3,1024)]=38
	offset_dict[(10002,1,4,3,512)] =10
	offset_dict[(10002,1,4,3,256)] =12
	offset_dict[(10002,1,4,3,128)] = 0

	offset_dict[(10002,1,4,4,2048)]=74
	offset_dict[(10002,1,4,4,1024)]=33
	offset_dict[(10002,1,4,4,512)] =14
	offset_dict[(10002,1,4,4,256)] = 9
	offset_dict[(10002,1,4,4,128)] = 0

	offset_dict[(10002,1,4,5,2048)]=58
	offset_dict[(10002,1,4,5,1024)]=32
	offset_dict[(10002,1,4,5,512)] =17
	offset_dict[(10002,1,4,5,256)] = 5
	offset_dict[(10002,1,4,5,128)] = 0

	offset_dict[(10002,1,4,6,2048)]=87
	offset_dict[(10002,1,4,6,1024)]=23
	offset_dict[(10002,1,4,6,512)] =13
	offset_dict[(10002,1,4,6,256)] = 9
	offset_dict[(10002,1,4,6,128)] = 0

	# TISC 10002
	# GLITC 1
	# Channel 5
	offset_dict[(10002,1,5,7,2048)]=68
	offset_dict[(10002,1,5,7,1024)]=31 
	offset_dict[(10002,1,5,7,512)] =20
	offset_dict[(10002,1,5,7,256)] = 4
	offset_dict[(10002,1,5,7,128)] = 0

	offset_dict[(10002,1,5,8,2048)]=69
	offset_dict[(10002,1,5,8,1024)]=31
	offset_dict[(10002,1,5,8,512)] =18
	offset_dict[(10002,1,5,8,256)] = 7
	offset_dict[(10002,1,5,8,128)] = 0

	offset_dict[(10002,1,5,9,2048)]=61 
	offset_dict[(10002,1,5,9,1024)]=22 
	offset_dict[(10002,1,5,9,512)] =15
	offset_dict[(10002,1,5,9,256)] =10
	offset_dict[(10002,1,5,9,128)] = 0

	offset_dict[(10002,1,5,10,2048)]=50
	offset_dict[(10002,1,5,10,1024)]=31
	offset_dict[(10002,1,5,10,512)] =17
	offset_dict[(10002,1,5,10,256)] =10
	offset_dict[(10002,1,5,10,128)] = 0

	offset_dict[(10002,1,5,11,2048)]=100
	offset_dict[(10002,1,5,11,1024)]=37
	offset_dict[(10002,1,5,11,512)] =13
	offset_dict[(10002,1,5,11,256)] = 7
	offset_dict[(10002,1,5,11,128)] = 0

	offset_dict[(10002,1,5,12,2048)]=88
	offset_dict[(10002,1,5,12,1024)]=29
	offset_dict[(10002,1,5,12,512)] =17
	offset_dict[(10002,1,5,12,256)] = 6
	offset_dict[(10002,1,5,12,128)] = 0

	offset_dict[(10002,1,5,13,2048)]=60
	offset_dict[(10002,1,5,13,1024)]=29
	offset_dict[(10002,1,5,13,512)] =15
	offset_dict[(10002,1,5,13,256)] = 6
	offset_dict[(10002,1,5,13,128)] = 0

	# TISC 10002
	# GLITC 1
	# Channel 6
	offset_dict[(10002,1,6,14,2048)]=89
	offset_dict[(10002,1,6,14,1024)]=41
	offset_dict[(10002,1,6,14,512)] =19
	offset_dict[(10002,1,6,14,256)] = 9
	offset_dict[(10002,1,6,14,128)] = 0

	offset_dict[(10002,1,6,15,2048)]=63
	offset_dict[(10002,1,6,15,1024)]=40
	offset_dict[(10002,1,6,15,512)] =14
	offset_dict[(10002,1,6,15,256)] = 7
	offset_dict[(10002,1,6,15,128)] = 0

	offset_dict[(10002,1,6,16,2048)]=44
	offset_dict[(10002,1,6,16,1024)]=25
	offset_dict[(10002,1,6,16,512)] =18
	offset_dict[(10002,1,6,16,256)] =11
	offset_dict[(10002,1,6,16,128)] = 0

	offset_dict[(10002,1,6,17,2048)]=49
	offset_dict[(10002,1,6,17,1024)]=19
	offset_dict[(10002,1,6,17,512)] =21
	offset_dict[(10002,1,6,17,256)] = 10
	offset_dict[(10002,1,6,17,128)] = 0

	offset_dict[(10002,1,6,18,2048)]=92
	offset_dict[(10002,1,6,18,1024)]=25
	offset_dict[(10002,1,6,18,512)] =11
	offset_dict[(10002,1,6,18,256)] =10
	offset_dict[(10002,1,6,18,128)] = 0

	offset_dict[(10002,1,6,19,2048)]=49
	offset_dict[(10002,1,6,19,1024)]=43
	offset_dict[(10002,1,6,19,512)] =18
	offset_dict[(10002,1,6,19,256)] =10
	offset_dict[(10002,1,6,19,128)] = 0

	offset_dict[(10002,1,6,20,2048)]=22 
	offset_dict[(10002,1,6,20,1024)]=22
	offset_dict[(10002,1,6,20,512)] =21
	offset_dict[(10002,1,6,20,256)] = 8
	offset_dict[(10002,1,6,20,128)] = 0


	#---------------------------------------
	#---------------GLITC 2-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 2
	# Channel 0
	offset_dict[(10002,2,0,0,2048)]=16
	offset_dict[(10002,2,0,0,1024)]=21
	offset_dict[(10002,2,0,0,512)] = 9
	offset_dict[(10002,2,0,0,256)] = 3
	offset_dict[(10002,2,0,0,128)] = 0

	offset_dict[(10002,2,0,1,2048)]=49
	offset_dict[(10002,2,0,1,1024)]=23
	offset_dict[(10002,2,0,1,512)] =10
	offset_dict[(10002,2,0,1,256)] = 4
	offset_dict[(10002,2,0,1,128)] = 0

	offset_dict[(10002,2,0,2,2048)]=67
	offset_dict[(10002,2,0,2,1024)]=26
	offset_dict[(10002,2,0,2,512)] =15
	offset_dict[(10002,2,0,2,256)] = 4
	offset_dict[(10002,2,0,2,128)] = 0

	offset_dict[(10002,2,0,3,2048)]=50
	offset_dict[(10002,2,0,3,1024)]=20
	offset_dict[(10002,2,0,3,512)] =14
	offset_dict[(10002,2,0,3,256)] = 1
	offset_dict[(10002,2,0,3,128)] = 0

	offset_dict[(10002,2,0,4,2048)]=39
	offset_dict[(10002,2,0,4,1024)]= 7 
	offset_dict[(10002,2,0,4,512)] = 9
	offset_dict[(10002,2,0,4,256)] = 7
	offset_dict[(10002,2,0,4,128)] = 0

	offset_dict[(10002,2,0,5,2048)]=33
	offset_dict[(10002,2,0,5,1024)]=27
	offset_dict[(10002,2,0,5,512)] =10
	offset_dict[(10002,2,0,5,256)] = 6
	offset_dict[(10002,2,0,5,128)] = 0

	offset_dict[(10002,2,0,6,2048)]=49
	offset_dict[(10002,2,0,6,1024)]=14
	offset_dict[(10002,2,0,6,512)] =20
	offset_dict[(10002,2,0,6,256)] = 6
	offset_dict[(10002,2,0,6,128)] = 0

	# TISC 10002
	# GLITC 2
	# Channel 1
	offset_dict[(10002,2,1,7,2048)]=44
	offset_dict[(10002,2,1,7,1024)]=10
	offset_dict[(10002,2,1,7,512)] = 3
	offset_dict[(10002,2,1,7,256)] = 9
	offset_dict[(10002,2,1,7,128)] = 0

	offset_dict[(10002,2,1,8,2048)]=64
	offset_dict[(10002,2,1,8,1024)]=33
	offset_dict[(10002,2,1,8,512)] =10
	offset_dict[(10002,2,1,8,256)] = 6
	offset_dict[(10002,2,1,8,128)] = 0

	offset_dict[(10002,2,1,9,2048)]=41
	offset_dict[(10002,2,1,9,1024)]=10
	offset_dict[(10002,2,1,9,512)] = 7
	offset_dict[(10002,2,1,9,256)] = 5
	offset_dict[(10002,2,1,9,128)] = 0

	offset_dict[(10002,2,1,10,2048)]=34
	offset_dict[(10002,2,1,10,1024)]=17
	offset_dict[(10002,2,1,10,512)] =12
	offset_dict[(10002,2,1,10,256)] = 3
	offset_dict[(10002,2,1,10,128)] = 0

	offset_dict[(10002,2,1,11,2048)]=10
	offset_dict[(10002,2,1,11,1024)]=26
	offset_dict[(10002,2,1,11,512)] =15
	offset_dict[(10002,2,1,11,256)] = 9
	offset_dict[(10002,2,1,11,128)] = 0

	offset_dict[(10002,2,1,12,2048)]=32
	offset_dict[(10002,2,1,12,1024)]=14
	offset_dict[(10002,2,1,12,512)] = 6
	offset_dict[(10002,2,1,12,256)] = 4
	offset_dict[(10002,2,1,12,128)] = 0

	offset_dict[(10002,2,1,13,2048)]=36
	offset_dict[(10002,2,1,13,1024)]=17
	offset_dict[(10002,2,1,13,512)] =16
	offset_dict[(10002,2,1,13,256)] = 9
	offset_dict[(10002,2,1,13,128)] = 0

	# TISC 10002
	# GLITC 2
	# Channel 2
	offset_dict[(10002,2,2,14,2048)]= 0 
	#^^This transition is missing codes!!^^ (Probably!!!)
	offset_dict[(10002,2,2,14,1024)]=24
	offset_dict[(10002,2,2,14,512)] = 5
	offset_dict[(10002,2,2,14,256)] = 2
	offset_dict[(10002,2,2,14,128)] = 0

	offset_dict[(10002,2,2,15,2048)]=67
	offset_dict[(10002,2,2,15,1024)]=23
	offset_dict[(10002,2,2,15,512)] = 7
	offset_dict[(10002,2,2,15,256)] = 6
	offset_dict[(10002,2,2,15,128)] = 0

	offset_dict[(10002,2,2,16,2048)]=46
	offset_dict[(10002,2,2,16,1024)]= 9
	offset_dict[(10002,2,2,16,512)] = 7
	offset_dict[(10002,2,2,16,256)] = 4
	offset_dict[(10002,2,2,16,128)] = 0

	offset_dict[(10002,2,2,17,2048)]=38
	offset_dict[(10002,2,2,17,1024)]= 0 
	#^^This transition is missing codes!!^^ (Probably only 1-3)
	offset_dict[(10002,2,2,17,512)] =12
	offset_dict[(10002,2,2,17,256)] = 4
	offset_dict[(10002,2,2,17,128)] = 0

	offset_dict[(10002,2,2,18,2048)]=50
	offset_dict[(10002,2,2,18,1024)]=20
	offset_dict[(10002,2,2,18,512)] = 7
	offset_dict[(10002,2,2,18,256)] = 8
	offset_dict[(10002,2,2,18,128)] = 0

	offset_dict[(10002,2,2,19,2048)]=51
	offset_dict[(10002,2,2,19,1024)]=16
	offset_dict[(10002,2,2,19,512)] =12
	offset_dict[(10002,2,2,19,256)] = 8
	offset_dict[(10002,2,2,19,128)] = 0

	offset_dict[(10002,2,2,20,2048)]=43
	offset_dict[(10002,2,2,20,1024)]=11
	offset_dict[(10002,2,2,20,512)] =10
	offset_dict[(10002,2,2,20,256)] = 5
	offset_dict[(10002,2,2,20,128)] = 0

	# TISC 10002
	# GLITC 2
	# Channel 4
	offset_dict[(10002,2,4,0,2048)]=53
	offset_dict[(10002,2,4,0,1024)]=31
	offset_dict[(10002,2,4,0,512)] =14 
	offset_dict[(10002,2,4,0,256)] = 7
	offset_dict[(10002,2,4,0,128)] = 0

	offset_dict[(10002,2,4,1,2048)]=21
	offset_dict[(10002,2,4,1,1024)]=13
	offset_dict[(10002,2,4,1,512)] =11
	offset_dict[(10002,2,4,1,256)] = 9
	offset_dict[(10002,2,4,1,128)] = 0

	offset_dict[(10002,2,4,2,2048)]=89 
	offset_dict[(10002,2,4,2,1024)]=32
	offset_dict[(10002,2,4,2,512)] =13
	offset_dict[(10002,2,4,2,256)] = 4
	offset_dict[(10002,2,4,2,128)] = 0

	offset_dict[(10002,2,4,3,2048)]=44 
	offset_dict[(10002,2,4,3,1024)]=23
	offset_dict[(10002,2,4,3,512)] =11
	offset_dict[(10002,2,4,3,256)] = 2
	offset_dict[(10002,2,4,3,128)] = 0

	offset_dict[(10002,2,4,4,2048)]=13
	offset_dict[(10002,2,4,4,1024)]= 3
	offset_dict[(10002,2,4,4,512)] =14
	offset_dict[(10002,2,4,4,256)] = 4
	offset_dict[(10002,2,4,4,128)] = 0

	offset_dict[(10002,2,4,5,2048)]=57
	offset_dict[(10002,2,4,5,1024)]=17
	offset_dict[(10002,2,4,5,512)] =13
	offset_dict[(10002,2,4,5,256)] = 5
	offset_dict[(10002,2,4,5,128)] = 0

	offset_dict[(10002,2,4,6,2048)]=12
	offset_dict[(10002,2,4,6,1024)]=22
	offset_dict[(10002,2,4,6,512)] =15
	offset_dict[(10002,2,4,6,256)] = 4
	offset_dict[(10002,2,4,6,128)] = 0

	# TISC 10002
	# GLITC 2
	# Channel 5
	offset_dict[(10002,2,5,7,2048)]=48
	offset_dict[(10002,2,5,7,1024)]=37
	offset_dict[(10002,2,5,7,512)] = 2
	offset_dict[(10002,2,5,7,256)] = 7
	offset_dict[(10002,2,5,7,128)] = 0

	offset_dict[(10002,2,5,8,2048)]=26
	offset_dict[(10002,2,5,8,1024)]=31
	offset_dict[(10002,2,5,8,512)] = 5
	offset_dict[(10002,2,5,8,256)] =12
	offset_dict[(10002,2,5,8,128)] = 0

	offset_dict[(10002,2,5,9,2048)]=41
	offset_dict[(10002,2,5,9,1024)]=20 
	offset_dict[(10002,2,5,9,512)] =11
	offset_dict[(10002,2,5,9,256)] = 3
	offset_dict[(10002,2,5,9,128)] = 0

	offset_dict[(10002,2,5,10,2048)]=59
	offset_dict[(10002,2,5,10,1024)]=44
	offset_dict[(10002,2,5,10,512)] = 3
	offset_dict[(10002,2,5,10,256)] = 3
	offset_dict[(10002,2,5,10,128)] = 0

	offset_dict[(10002,2,5,11,2048)]=36
	offset_dict[(10002,2,5,11,1024)]=22
	offset_dict[(10002,2,5,11,512)] =14
	offset_dict[(10002,2,5,11,256)] = 7
	offset_dict[(10002,2,5,11,128)] = 0

	offset_dict[(10002,2,5,12,2048)]=48
	offset_dict[(10002,2,5,12,1024)]= 7 
	offset_dict[(10002,2,5,12,512)] = 7
	offset_dict[(10002,2,5,12,256)] = 6
	offset_dict[(10002,2,5,12,128)] = 0

	offset_dict[(10002,2,5,13,2048)]=54
	offset_dict[(10002,2,5,13,1024)]=21
	offset_dict[(10002,2,5,13,512)] =15
	offset_dict[(10002,2,5,13,256)] = 5
	offset_dict[(10002,2,5,13,128)] = 0

	# TISC 10002
	# GLITC 2
	# Channel 6
	offset_dict[(10002,2,6,14,2048)]=40
	offset_dict[(10002,2,6,14,1024)]=35
	offset_dict[(10002,2,6,14,512)] = 11
	offset_dict[(10002,2,6,14,256)] = 6
	offset_dict[(10002,2,6,14,128)] = 0

	offset_dict[(10002,2,6,15,2048)]=44
	offset_dict[(10002,2,6,15,1024)]=43
	offset_dict[(10002,2,6,15,512)] =21
	offset_dict[(10002,2,6,15,256)] = 4
	offset_dict[(10002,2,6,15,128)] = 0

	offset_dict[(10002,2,6,16,2048)]=45
	offset_dict[(10002,2,6,16,1024)]=29
	offset_dict[(10002,2,6,16,512)] =10
	offset_dict[(10002,2,6,16,256)] = 5
	offset_dict[(10002,2,6,16,128)] = 0

	offset_dict[(10002,2,6,17,2048)]=21
	offset_dict[(10002,2,6,17,1024)]=21
	offset_dict[(10002,2,6,17,512)] =10
	offset_dict[(10002,2,6,17,256)] = 4
	offset_dict[(10002,2,6,17,128)] = 0

	offset_dict[(10002,2,6,18,2048)]=33 
	offset_dict[(10002,2,6,18,1024)]=35
	offset_dict[(10002,2,6,18,512)] =10
	offset_dict[(10002,2,6,18,256)] = 4
	offset_dict[(10002,2,6,18,128)] = 0

	offset_dict[(10002,2,6,19,2048)]=12 
	offset_dict[(10002,2,6,19,1024)]=28
	offset_dict[(10002,2,6,19,512)] =15
	offset_dict[(10002,2,6,19,256)] = 7
	offset_dict[(10002,2,6,19,128)] = 0

	offset_dict[(10002,2,6,20,2048)]=37
	offset_dict[(10002,2,6,20,1024)]=24
	offset_dict[(10002,2,6,20,512)] =12
	offset_dict[(10002,2,6,20,256)] = 9
	offset_dict[(10002,2,6,20,128)] = 0

	
	#---------------------------------------
	#---------------GLITC 3-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 3
	# Channel 0
	offset_dict[(10002,3,0,0,2048)]=48
	offset_dict[(10002,3,0,0,1024)]=31
	offset_dict[(10002,3,0,0,512)] =16
	offset_dict[(10002,3,0,0,256)] = 4
	offset_dict[(10002,3,0,0,128)] = 0

	offset_dict[(10002,3,0,1,2048)]=35
	offset_dict[(10002,3,0,1,1024)]=26 
	offset_dict[(10002,3,0,1,512)] =15
	offset_dict[(10002,3,0,1,256)] = 7
	offset_dict[(10002,3,0,1,128)] = 0

	offset_dict[(10002,3,0,2,2048)]=83
	offset_dict[(10002,3,0,2,1024)]=37
	offset_dict[(10002,3,0,2,512)] =23
	offset_dict[(10002,3,0,2,256)] =10
	offset_dict[(10002,3,0,2,128)] = 0

	offset_dict[(10002,3,0,3,2048)]=57
	offset_dict[(10002,3,0,3,1024)]=39
	offset_dict[(10002,3,0,3,512)] =21
	offset_dict[(10002,3,0,3,256)] = 0
	offset_dict[(10002,3,0,3,128)] = 0

	offset_dict[(10002,3,0,4,2048)]=72
	offset_dict[(10002,3,0,4,1024)]=31
	offset_dict[(10002,3,0,4,512)] =13
	offset_dict[(10002,3,0,4,256)] = 8
	offset_dict[(10002,3,0,4,128)] = 0

	offset_dict[(10002,3,0,5,2048)]=76
	offset_dict[(10002,3,0,5,1024)]=27
	offset_dict[(10002,3,0,5,512)] =22
	offset_dict[(10002,3,0,5,256)] = 2
	offset_dict[(10002,3,0,5,128)] = 0

	offset_dict[(10002,3,0,6,2048)]=66
	offset_dict[(10002,3,0,6,1024)]=30
	offset_dict[(10002,3,0,6,512)] =19
	offset_dict[(10002,3,0,6,256)] = 8
	offset_dict[(10002,3,0,6,128)] = 0

	# TISC 10002
	# GLITC 3
	# Channel 1
	offset_dict[(10002,3,1,7,2048)]=40
	offset_dict[(10002,3,1,7,1024)]=34
	offset_dict[(10002,3,1,7,512)] =21
	offset_dict[(10002,3,1,7,256)] = 8
	offset_dict[(10002,3,1,7,128)] = 0

	offset_dict[(10002,3,1,8,2048)]=55
	offset_dict[(10002,3,1,8,1024)]=36 
	offset_dict[(10002,3,1,8,512)] = 9
	offset_dict[(10002,3,1,8,256)] = 1
	offset_dict[(10002,3,1,8,128)] = 0

	offset_dict[(10002,3,1,9,2048)]=62
	offset_dict[(10002,3,1,9,1024)]=25
	offset_dict[(10002,3,1,9,512)] =17
	offset_dict[(10002,3,1,9,256)] = 8
	offset_dict[(10002,3,1,9,128)] = 0

	offset_dict[(10002,3,1,10,2048)]=52
	offset_dict[(10002,3,1,10,1024)]=32
	offset_dict[(10002,3,1,10,512)] =22
	offset_dict[(10002,3,1,10,256)] =13
	offset_dict[(10002,3,1,10,128)] = 0

	offset_dict[(10002,3,1,11,2048)]=58
	offset_dict[(10002,3,1,11,1024)]=15
	offset_dict[(10002,3,1,11,512)] =12
	offset_dict[(10002,3,1,11,256)] =10
	offset_dict[(10002,3,1,11,128)] = 0

	offset_dict[(10002,3,1,12,2048)]=57
	offset_dict[(10002,3,1,12,1024)]=17
	offset_dict[(10002,3,1,12,512)] =15
	offset_dict[(10002,3,1,12,256)] = 9
	offset_dict[(10002,3,1,12,128)] = 0

	offset_dict[(10002,3,1,13,2048)]=87
	offset_dict[(10002,3,1,13,1024)]=27
	offset_dict[(10002,3,1,13,512)] =12
	offset_dict[(10002,3,1,13,256)] = 7
	offset_dict[(10002,3,1,13,128)] = 0

	# TISC 10002
	# GLITC 3
	# Channel 2
	offset_dict[(10002,3,2,14,2048)]=92
	offset_dict[(10002,3,2,14,1024)]=22
	offset_dict[(10002,3,2,14,512)] =13
	offset_dict[(10002,3,2,14,256)] = 7
	offset_dict[(10002,3,2,14,128)] = 0

	offset_dict[(10002,3,2,15,2048)]=56
	offset_dict[(10002,3,2,15,1024)]=20 
	offset_dict[(10002,3,2,15,512)] =13
	offset_dict[(10002,3,2,15,256)] = 8 
	offset_dict[(10002,3,2,15,128)] = 0

	offset_dict[(10002,3,2,16,2048)]=72
	offset_dict[(10002,3,2,16,1024)]=23
	offset_dict[(10002,3,2,16,512)] =16
	offset_dict[(10002,3,2,16,256)] = 4
	offset_dict[(10002,3,2,16,128)] = 0

	offset_dict[(10002,3,2,17,2048)]=70
	offset_dict[(10002,3,2,17,1024)]=33
	offset_dict[(10002,3,2,17,512)] =22
	offset_dict[(10002,3,2,17,256)] = 6
	offset_dict[(10002,3,2,17,128)] = 0

	offset_dict[(10002,3,2,18,2048)]=77
	offset_dict[(10002,3,2,18,1024)]=47
	offset_dict[(10002,3,2,18,512)] =14
	offset_dict[(10002,3,2,18,256)] = 8
	offset_dict[(10002,3,2,18,128)] = 0

	offset_dict[(10002,3,2,19,2048)]=66
	offset_dict[(10002,3,2,19,1024)]=40
	offset_dict[(10002,3,2,19,512)] =21
	offset_dict[(10002,3,2,19,256)] = 5
	offset_dict[(10002,3,2,19,128)] = 0

	offset_dict[(10002,3,2,20,2048)]=65
	offset_dict[(10002,3,2,20,1024)]=36
	offset_dict[(10002,3,2,20,512)] =15
	offset_dict[(10002,3,2,20,256)] =11
	offset_dict[(10002,3,2,20,128)] = 0

	# TISC 10002
	# GLITC 3
	# Channel 4
	offset_dict[(10002,3,4,0,2048)]=67
	offset_dict[(10002,3,4,0,1024)]=38
	offset_dict[(10002,3,4,0,512)] =18
	offset_dict[(10002,3,4,0,256)] =12
	offset_dict[(10002,3,4,0,128)] = 0

	offset_dict[(10002,3,4,1,2048)]=47
	offset_dict[(10002,3,4,1,1024)]=29
	offset_dict[(10002,3,4,1,512)] =14
	offset_dict[(10002,3,4,1,256)] =11
	offset_dict[(10002,3,4,1,128)] = 0

	offset_dict[(10002,3,4,2,2048)]=64
	offset_dict[(10002,3,4,2,1024)]=36
	offset_dict[(10002,3,4,2,512)] =14
	offset_dict[(10002,3,4,2,256)] =10
	offset_dict[(10002,3,4,2,128)] = 0

	offset_dict[(10002,3,4,3,2048)]=71
	offset_dict[(10002,3,4,3,1024)]=44
	offset_dict[(10002,3,4,3,512)] =12
	offset_dict[(10002,3,4,3,256)] = 6
	offset_dict[(10002,3,4,3,128)] = 0

	offset_dict[(10002,3,4,4,2048)]=27
	offset_dict[(10002,3,4,4,1024)]=40
	offset_dict[(10002,3,4,4,512)] =18
	offset_dict[(10002,3,4,4,256)] = 9
	offset_dict[(10002,3,4,4,128)] = 0

	offset_dict[(10002,3,4,5,2048)]=50
	offset_dict[(10002,3,4,5,1024)]=46
	offset_dict[(10002,3,4,5,512)] =11
	offset_dict[(10002,3,4,5,256)] = 9
	offset_dict[(10002,3,4,5,128)] = 0

	offset_dict[(10002,3,4,6,2048)]=60
	offset_dict[(10002,3,4,6,1024)]=20
	offset_dict[(10002,3,4,6,512)] =13
	offset_dict[(10002,3,4,6,256)] = 6
	offset_dict[(10002,3,4,6,128)] = 0

	# TISC 10002
	# GLITC 3
	# Channel 5
	offset_dict[(10002,3,5,7,2048)]=83
	offset_dict[(10002,3,5,7,1024)]=31 
	offset_dict[(10002,3,5,7,512)] =11
	offset_dict[(10002,3,5,7,256)] = 9
	offset_dict[(10002,3,5,7,128)] = 0

	offset_dict[(10002,3,5,8,2048)]=52
	offset_dict[(10002,3,5,8,1024)]=31
	offset_dict[(10002,3,5,8,512)] =13
	offset_dict[(10002,3,5,8,256)] = 7
	offset_dict[(10002,3,5,8,128)] = 0

	offset_dict[(10002,3,5,9,2048)]=75
	offset_dict[(10002,3,5,9,1024)]=34
	offset_dict[(10002,3,5,9,512)] =17
	offset_dict[(10002,3,5,9,256)] = 7
	offset_dict[(10002,3,5,9,128)] = 0

	offset_dict[(10002,3,5,10,2048)]=74
	offset_dict[(10002,3,5,10,1024)]=27
	offset_dict[(10002,3,5,10,512)] =20
	offset_dict[(10002,3,5,10,256)] = 7
	offset_dict[(10002,3,5,10,128)] = 0

	offset_dict[(10002,3,5,11,2048)]=60
	offset_dict[(10002,3,5,11,1024)]=22
	offset_dict[(10002,3,5,11,512)] =14
	offset_dict[(10002,3,5,11,256)] =10
	offset_dict[(10002,3,5,11,128)] = 0

	offset_dict[(10002,3,5,12,2048)]=70
	offset_dict[(10002,3,5,12,1024)]=27
	offset_dict[(10002,3,5,12,512)] =20
	offset_dict[(10002,3,5,12,256)] = 5
	offset_dict[(10002,3,5,12,128)] = 0

	offset_dict[(10002,3,5,13,2048)]=68
	offset_dict[(10002,3,5,13,1024)]=33
	offset_dict[(10002,3,5,13,512)] =18
	offset_dict[(10002,3,5,13,256)] = 5
	offset_dict[(10002,3,5,13,128)] = 0
	"""
	# TISC 10002
	# GLITC 3
	# Channel 6
	offset_dict[(10002,3,6,14,2048)]=
	offset_dict[(10002,3,6,14,1024)]=
	offset_dict[(10002,3,6,14,512)] = 
	offset_dict[(10002,3,6,14,256)] = 0
	offset_dict[(10002,3,6,14,128)] = 0

	offset_dict[(10002,3,6,15,2048)]=
	offset_dict[(10002,3,6,15,1024)]=
	offset_dict[(10002,3,6,15,512)] =
	offset_dict[(10002,3,6,15,256)] = 0
	offset_dict[(10002,3,6,15,128)] = 0

	offset_dict[(10002,3,6,16,2048)]=
	offset_dict[(10002,3,6,16,1024)]=
	offset_dict[(10002,3,6,16,512)] =
	offset_dict[(10002,3,6,16,256)] = 0
	offset_dict[(10002,3,6,16,128)] = 0

	offset_dict[(10002,3,6,17,2048)]=
	offset_dict[(10002,3,6,17,1024)]=
	offset_dict[(10002,3,6,17,512)] =
	offset_dict[(10002,3,6,17,256)] = 0
	offset_dict[(10002,3,6,17,128)] = 0

	offset_dict[(10002,3,6,18,2048)]=
	offset_dict[(10002,3,6,18,1024)]=
	offset_dict[(10002,3,6,18,512)] =
	offset_dict[(10002,3,6,18,256)] = 0
	offset_dict[(10002,3,6,18,128)] = 0

	offset_dict[(10002,3,6,19,2048)]=
	offset_dict[(10002,3,6,19,1024)]=
	offset_dict[(10002,3,6,19,512)] =
	offset_dict[(10002,3,6,19,256)] = 0
	offset_dict[(10002,3,6,19,128)] = 0

	offset_dict[(10002,3,6,20,2048)]=
	offset_dict[(10002,3,6,20,1024)]=
	offset_dict[(10002,3,6,20,512)] =
	offset_dict[(10002,3,6,20,256)] = 0
	offset_dict[(10002,3,6,20,128)] = 0
	"""


	
	return offset_dict[(TISC_n,GLITC_n,channel,RITC_DAC_Number,2048)],offset_dict[(TISC_n,GLITC_n,channel,RITC_DAC_Number,1024)],offset_dict[(TISC_n,GLITC_n,channel,RITC_DAC_Number,512)],offset_dict[(TISC_n,GLITC_n,channel,RITC_DAC_Number,256)],offset_dict[(TISC_n,GLITC_n,channel,RITC_DAC_Number,128)]


#if "__name__" == __main__:
	#print offset_dict[(2,0,0,5,512)]
