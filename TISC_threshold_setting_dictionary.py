
def get_threshold(TISC_n,GLITC_n,channel,RITC_COMP):
	thresh_dict = {}

	# Syntax (TISC_Number,GLITC_Number,Channel_Number,RITC_DAC_Number) = transition_setting

	#Note, Steps of 40 dac counts between thresholds may be unnessesary.  It was sort of arbritrary. 
	#Tryed to keep to middle of good range (which is best all the time) and inside ideal range for all.


	#---------------------------------------
	#---------------GLITC 0-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 0
	# Channel 0
	
	# Expanded high end, Th4 set to 760
	#print "setting things"
	
	thresh_dict[(10002,0,0,0)] = 1871
	thresh_dict[(10002,0,0,1)] = 1816
	thresh_dict[(10002,0,0,2)] = 1733
	thresh_dict[(10002,0,0,3)] = 1622
	thresh_dict[(10002,0,0,4)] = 1482
	thresh_dict[(10002,0,0,5)] = 1314
	thresh_dict[(10002,0,0,6)] = 1117
	"""
	# Th4 set to 760 only
	thresh_dict[(10002,0,0,0)] = 1779
	thresh_dict[(10002,0,0,1)] = 1709
	thresh_dict[(10002,0,0,2)] = 1623
	thresh_dict[(10002,0,0,3)] = 1521
	thresh_dict[(10002,0,0,4)] = 1403
	thresh_dict[(10002,0,0,5)] = 1269
	thresh_dict[(10002,0,0,6)] = 1118
	"""
	# TISC 10002
	# GLITC 0
	# Channel 1
	thresh_dict[(10002,0,1,7)] =  2003#1857
	thresh_dict[(10002,0,1,8)] =  1906#1742
	thresh_dict[(10002,0,1,9)] =  1805#1621
	thresh_dict[(10002,0,1,10)] = 1701#1496
	thresh_dict[(10002,0,1,11)] = 1592#1366
	thresh_dict[(10002,0,1,12)] = 1480#1230
	thresh_dict[(10002,0,1,13)] = 1364#1090

	# TISC 10002
	# GLITC 0
	# Channel 2
	thresh_dict[(10002,0,2,14)] = 1982
	thresh_dict[(10002,0,2,15)] = 1896
	thresh_dict[(10002,0,2,16)] = 1803
	thresh_dict[(10002,0,2,17)] = 1703
	thresh_dict[(10002,0,2,18)] = 1596
	thresh_dict[(10002,0,2,19)] = 1481
	thresh_dict[(10002,0,2,20)] = 1360

	# TISC 10002
	# GLITC 0
	# Channel 4
	thresh_dict[(10002,0,4,0)] = 1933
	thresh_dict[(10002,0,4,1)] = 1857
	thresh_dict[(10002,0,4,2)] = 1770 # One bad sample, probably sample 31
	thresh_dict[(10002,0,4,3)] = 1672
	thresh_dict[(10002,0,4,4)] = 1563
	thresh_dict[(10002,0,4,5)] = 1443
	thresh_dict[(10002,0,4,6)] = 1311

	# TISC 10002
	# GLITC 0
	# Channel 5
	thresh_dict[(10002,0,5,7)] =  1966
	thresh_dict[(10002,0,5,8)] =  1888
	thresh_dict[(10002,0,5,9)] =  1801 # Two bad samples
	thresh_dict[(10002,0,5,10)] = 1704
	thresh_dict[(10002,0,5,11)] = 1597
	thresh_dict[(10002,0,5,12)] = 1481
	thresh_dict[(10002,0,5,13)] = 1355

	# TISC 10002
	# GLITC 0
	# Channel 6
	thresh_dict[(10002,0,6,14)] = 1990
	thresh_dict[(10002,0,6,15)] = 1904 
	thresh_dict[(10002,0,6,16)] = 1810
	thresh_dict[(10002,0,6,17)] = 1707
	thresh_dict[(10002,0,6,18)] = 1596
	thresh_dict[(10002,0,6,19)] = 1476 
	thresh_dict[(10002,0,6,20)] = 1349


	#---------------------------------------
	#---------------GLITC 1-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 1
	# Channel 0
	thresh_dict[(10002,1,0,0)] = 1953
	thresh_dict[(10002,1,0,1)] = 1876
	thresh_dict[(10002,1,0,2)] = 1794
	thresh_dict[(10002,1,0,3)] = 1710
	thresh_dict[(10002,1,0,4)] = 1623
	thresh_dict[(10002,1,0,5)] = 1532
	thresh_dict[(10002,1,0,6)] = 1438

	# TISC 10002
	# GLITC 1
	# Channel 1
	thresh_dict[(10002,1,1,7)] = 1874
	thresh_dict[(10002,1,1,8)] = 1819
	thresh_dict[(10002,1,1,9)] = 1756
	thresh_dict[(10002,1,1,10)] = 1686
	thresh_dict[(10002,1,1,11)] = 1608
	thresh_dict[(10002,1,1,12)] = 1523
	thresh_dict[(10002,1,1,13)] = 1430

	# TISC 10002
	# GLITC 1
	# Channel 2
	thresh_dict[(10002,1,2,14)] = 1981
	thresh_dict[(10002,1,2,15)] = 1898
	thresh_dict[(10002,1,2,16)] = 1806
	thresh_dict[(10002,1,2,17)] = 1702
	thresh_dict[(10002,1,2,18)] = 1588
	thresh_dict[(10002,1,2,19)] = 1464
	thresh_dict[(10002,1,2,20)] = 1330

	# TISC 10002
	# GLITC 1
	# Channel 4
	thresh_dict[(10002,1,4,0)] = 1969
	thresh_dict[(10002,1,4,1)] = 1874
	thresh_dict[(10002,1,4,2)] = 1772
	thresh_dict[(10002,1,4,3)] = 1664
	thresh_dict[(10002,1,4,4)] = 1550
	thresh_dict[(10002,1,4,5)] = 1428
	thresh_dict[(10002,1,4,6)] = 1300

	# TISC 10002
	# GLITC 1
	# Channel 5
	thresh_dict[(10002,1,5,7)] = 1907
	thresh_dict[(10002,1,5,8)] = 1852
	thresh_dict[(10002,1,5,9)] = 1784
	thresh_dict[(10002,1,5,10)] = 1700
	thresh_dict[(10002,1,5,11)] = 1602
	thresh_dict[(10002,1,5,12)] = 1489
	thresh_dict[(10002,1,5,13)] = 1361

	# TISC 10002
	# GLITC 1
	# Channel 6
	thresh_dict[(10002,1,6,14)] = 1977
	thresh_dict[(10002,1,6,15)] = 1888
	thresh_dict[(10002,1,6,16)] = 1791
	thresh_dict[(10002,1,6,17)] = 1687
	thresh_dict[(10002,1,6,18)] = 1576
	thresh_dict[(10002,1,6,19)] = 1458
	thresh_dict[(10002,1,6,20)] = 1332


	#---------------------------------------
	#---------------GLITC 2-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 2
	# Channel 0
	thresh_dict[(10002,2,0,0)] = 1929
	thresh_dict[(10002,2,0,1)] = 1854
	thresh_dict[(10002,2,0,2)] = 1776
	thresh_dict[(10002,2,0,3)] = 1696
	thresh_dict[(10002,2,0,4)] = 1613
	thresh_dict[(10002,2,0,5)] = 1528
	thresh_dict[(10002,2,0,6)] = 1440

	# TISC 10002
	# GLITC 2
	# Channel 1
	thresh_dict[(10002,2,1,7)] = 1867
	thresh_dict[(10002,2,1,8)] = 1814
	thresh_dict[(10002,2,1,9)] = 1759
	thresh_dict[(10002,2,1,10)] = 1704
	thresh_dict[(10002,2,1,11)] = 1648
	thresh_dict[(10002,2,1,12)] = 1591
	thresh_dict[(10002,2,1,13)] = 1533

	# TISC 10002
	# GLITC 2
	# Channel 2
	thresh_dict[(10002,2,2,14)] = 2074
	thresh_dict[(10002,2,2,15)] = 1961
	thresh_dict[(10002,2,2,16)] = 1848
	thresh_dict[(10002,2,2,17)] = 1732
	thresh_dict[(10002,2,2,18)] = 1616
	thresh_dict[(10002,2,2,19)] = 1498
	thresh_dict[(10002,2,2,20)] = 1379

	# TISC 10002
	# GLITC 2
	# Channel 4
	thresh_dict[(10002,2,4,0)] = 1907
	thresh_dict[(10002,2,4,1)] = 1843
	thresh_dict[(10002,2,4,2)] = 1775
	thresh_dict[(10002,2,4,3)] = 1703
	thresh_dict[(10002,2,4,4)] = 1626
	thresh_dict[(10002,2,4,5)] = 1546
	thresh_dict[(10002,2,4,6)] = 1460

	# TISC 10002
	# GLITC 2
	# Channel 5
	thresh_dict[(10002,2,5,7)] = 1857
	thresh_dict[(10002,2,5,8)] = 1804
	thresh_dict[(10002,2,5,9)] = 1751
	thresh_dict[(10002,2,5,10)] = 1698
	thresh_dict[(10002,2,5,11)] = 1644
	thresh_dict[(10002,2,5,12)] = 1590
	thresh_dict[(10002,2,5,13)] = 1535

	# TISC 10002
	# GLITC 2
	# Channel 6
	thresh_dict[(10002,2,6,14)] = 1975
	thresh_dict[(10002,2,6,15)] = 1900
	thresh_dict[(10002,2,6,16)] = 1823
	thresh_dict[(10002,2,6,17)] = 1744
	thresh_dict[(10002,2,6,18)] = 1662
	thresh_dict[(10002,2,6,19)] = 1579
	thresh_dict[(10002,2,6,20)] = 1494


	
	#---------------------------------------
	#---------------GLITC 3-----------------
	#---------------------------------------


	# TISC 10002
	# GLITC 3
	# Channel 0
	thresh_dict[(10002,3,0,0)] = 2030
	thresh_dict[(10002,3,0,1)] = 1918
	thresh_dict[(10002,3,0,2)] = 1806
	thresh_dict[(10002,3,0,3)] = 1695
	thresh_dict[(10002,3,0,4)] = 1585
	thresh_dict[(10002,3,0,5)] = 1477
	thresh_dict[(10002,3,0,6)] = 1367

	# TISC 10002
	# GLITC 3
	# Channel 1
	thresh_dict[(10002,3,1,7)] = 1972
	thresh_dict[(10002,3,1,8)] = 1889
	thresh_dict[(10002,3,1,9)] = 1796
	thresh_dict[(10002,3,1,10)] = 1693
	thresh_dict[(10002,3,1,11)] = 1581
	thresh_dict[(10002,3,1,12)] = 1459
	thresh_dict[(10002,3,1,13)] = 1328

	# TISC 10002
	# GLITC 3
	# Channel 2
	thresh_dict[(10002,3,2,14)] = 1914
	thresh_dict[(10002,3,2,15)] = 1843
	thresh_dict[(10002,3,2,16)] = 1769
	thresh_dict[(10002,3,2,17)] = 1690
	thresh_dict[(10002,3,2,18)] = 1608
	thresh_dict[(10002,3,2,19)] = 1522
	thresh_dict[(10002,3,2,20)] = 1432

	# TISC 10002
	# GLITC 3
	# Channel 4
	thresh_dict[(10002,3,4,0)] = 1949
	thresh_dict[(10002,3,4,1)] = 1856
	thresh_dict[(10002,3,4,2)] = 1757
	thresh_dict[(10002,3,4,3)] = 1653
	thresh_dict[(10002,3,4,4)] = 1543
	thresh_dict[(10002,3,4,5)] = 1428
	thresh_dict[(10002,3,4,6)] = 1307

	# TISC 10002
	# GLITC 3
	# Channel 5
	thresh_dict[(10002,3,5,7)] = 2003
	thresh_dict[(10002,3,5,8)] = 1902
	thresh_dict[(10002,3,5,9)] = 1789
	thresh_dict[(10002,3,5,10)] = 1663
	thresh_dict[(10002,3,5,11)] = 1525
	thresh_dict[(10002,3,5,12)] = 1374
	thresh_dict[(10002,3,5,13)] = 1210

	"""
	# TISC 10002
	# GLITC 3
	# Channel 6
	thresh_dict[(10002,3,6,14)] = 0
	thresh_dict[(10002,3,6,15)] = 0
	thresh_dict[(10002,3,6,16)] = 0
	thresh_dict[(10002,3,6,17)] = 0
	thresh_dict[(10002,3,6,18)] = 0
	thresh_dict[(10002,3,6,19)] = 0
	thresh_dict[(10002,3,6,20)] = 0
	"""


	return thresh_dict[(TISC_n,GLITC_n,channel,RITC_COMP)]


#if "__name__" == __main__:
	#print thresh_dict[(2,0,0,5)]
