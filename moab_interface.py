#!/usr/bin/env python3
  
import select
import socket
import struct
import time
import pickle


def DriveWheels(sbus_throttle, sbus_steering):
	## this is atdrive-moab on branch "XWheels-dev-SBUS_throttle_steering"
	## we send back sbus_throttle and steering instead of rpmR rpmL
	udpPacket = struct.pack('HH', sbus_throttle, sbus_steering)
	moab_sock.sendto(udpPacket, (MOAB_COMPUTER, MOAB_PORT))
	

######################### UDP ############################
MOAB_COMPUTER = "192.168.10.20"
MOAB_PORT = 12346
moab_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

SBUS_RX_PORT = 31338
sbus_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
sbus_sock.bind(("0.0.0.0", SBUS_RX_PORT))
sbus_sock.setblocking(0)

SLU_RC_PORT = 7777
slu_rc_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)

MOAB_CONSOLE_PORT = 5555
moab_console_sock = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
moab_console_sock.bind(("0.0.0.0", MOAB_CONSOLE_PORT))
moab_console_sock.setblocking(0)

######################### Parameter ###########################
sbus_mid = 1018
sbus_inc = 300	# limit is 580

######################### Loop ###########################
STR_val = 0.0
THR_val = 0.0
got_data_time = time.time()
got_sbus_time = time.time()
sbus_throttle = sbus_mid
sbus_steering = sbus_mid

while True:

	##############################################
	################# SBUS Parser ################
	##############################################
	try:
		pkt, addr = sbus_sock.recvfrom(64)
		got_sbus_time = time.time()
	except socket.error:
		## This is safety timeout, if there SBUS got disconnected somehow, just set it back to mid
		## But it's rarely happened, because atdrive-moab firmware has a detection for SBUS communication lost
		## So MOAB will set eveything to middle quicker
		last_got_sbus_period = time.time() - got_sbus_time
		if (last_got_sbus_period > 0.5) and (sbus_throttle != sbus_mid or sbus_steering != sbus_mid):
			print("DANGER...SBUS on moab got disconnected sbus_steering was {:} sbus_throttle was {:}".format(sbus_steering,sbus_throttle))
			sbus_throttle = sbus_mid
			sbus_steering = sbus_mid
			DriveWheels(sbus_throttle, sbus_steering)
		pass
	else:
		if len(pkt) < 16:
			print("Error:  short packet.  len:", len(pkt))
		else:
			try:
				ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8, \
				ch9, ch10, ch11, ch12, ch13, ch14, ch15, ch16, \
				failsafe, frame_lost = struct.unpack("HHHHHHHHHHHHHHHH??", pkt[:34])
			except Exception as e:
				print("failed to parse packet:", e)
			else:
				# print(ch1, ch2, ch3, ch4, ch5, ch6, ch7, ch8,ch9, ch10, ch11, ch12, ch13, ch14, ch15, ch16, failsafe, frame_lost)

				## In auto mode
				if (ch7 > 1050 and ch7 < 1100) and (ch8 > 1050 and ch8 < 1100):

					DriveWheels(sbus_throttle, sbus_steering)

	###################################################
	################# Get gamepad data ################
	###################################################
	try:
		data, addr = moab_console_sock.recvfrom(1024)
		# print("data len", len(data))
		data = pickle.loads(data)
		got_data_time = time.time()
	except socket.error:
		## This is safety timeout, if there is data piling somewhere, we quickly set STR and THR to 0.0
		last_got_period = time.time() - got_data_time
		if (last_got_period > 0.5) and (STR_val != 0 or THR_val != 0):
			print("DANGER...gamepad data is piling... STR was {:} THR was {:}".format(STR_val,THR_val))
			STR_val = 0.0
			THR_val = 0.0
			sbus_throttle = sbus_mid
			sbus_steering = sbus_mid
			DriveWheels(sbus_throttle, sbus_steering)
		pass
	else:
		print(data)
		STR_val = data['STR_VAL']
		THR_val = data['THR_VAL']
		sbus_steering = int(round(STR_val*sbus_inc + sbus_mid))
		sbus_throttle = int(round(THR_val*sbus_inc + sbus_mid))



	# print("Here")



	time.sleep(0.0001)






