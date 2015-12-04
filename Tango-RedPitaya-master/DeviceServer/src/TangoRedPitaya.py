# -*- coding: utf-8 -*-

## Tango-RedPitaya -- Tango device server for RedPitaya multi-istrument board
## Solaris <synchrotron.pl>



from PyTango import AttrQuality, AttrWriteType, AttrDataFormat, DispLevel, DevState
from PyTango.server import Device, DeviceMeta
from PyTango.server import attribute, command, device_property

from PyRedPitaya.pc import RedPitaya
from rpyc import connect

from urllib2 import urlopen
import json
import re
from __builtin__ import str
from numpy import integer


class RedPitayaBoard(Device):
	""" RedPitaya device server class """
	__metaclass__ = DeviceMeta


	### RPyC connection details -----------------------------------------------
	name = device_property(dtype=str)							# board name
	host = device_property(dtype=str)							# board ip
	port = device_property(dtype=int, default_value=18861)		# board port
	nfs_ip = device_property(dtype=str)							# nfs ip
	mnt_point = device_property(dtype=str)						# mnt point
	reconnect = device_property(dtype=int, default_value=30)	# max reconnect attempts


	### Utilities -------------------------------------------------------------

	def connection_error(self, e):
		""" Set status message informing about connection error and appropiate state """
		self._state = DevState.FAULT
		self.status_message = "Could not connect to the board @ %s:%d\nError message: %s\n" % (self.host, self.port, str(e))
		self.status_message += "Reconnect attempt %d / %d\n" % (self.reconnect_tries, self.reconnect)
		if self.reconnect_tries == self.reconnect:
			self.status_message += "Not trying again."

	def nfs_error(self, e):
		""" Set status message informing about web application error """
		self._state = DevState.STANDBY
		self.status_message = "Could not connect to nfs at %s. Error message: %s\n" % (self.host, str(e))

	def app_error(self, e):
		""" Set status message informing about web application error """
		self._state = DevState.STANDBY
		self.status_message = "Could not connect to webapp @ %s. Error message: %s\n" % (self.host, str(e))
		self.status_message += "You need to have scope (Oscilloscope) webapp installed on your device.\n"
		self.status_message += "Only input acquisition is affected, you can use all other functions anyway."

	def set_state_ok(self, state):
		""" Sets state of normal operation and clears status message """
		self._state = state
		self.status_message = ""

	def mount_nfs(self):
		try:
			command = "mount.nfs %s:%s /mnt" % (self.nfs_ip, self.mnt_point)
			print command
			self.conn.root.run_command(command)
		except Exception as e:
			self.connection_error(e)

	def board_connect(self):
		""" Connect to the board """
		try:
			self.conn = connect(self.host, self.port)
			self.RP = RedPitaya(self.conn)
			self.mount_nfs()
			self.set_state_ok(DevState.STANDBY)
		except Exception as e:
			self.connection_error(e)

	def start_generator(self, channel, opts):
		""" Start signal generator decribed by opts on desired output channel.
			Purpose of this function is to minimize argument count (and therefore mistake possibilities)
			to the Tango accessible generator functions """
		# data sanity check
		m = re.match(r"(\d+(\.\d+)?) (\d+(\.\d+)?) (.*)", opts)
		if not m:
			self.status_message = "Error: Invalid generator arguments format.\nShould be: Vpp Frequency Type"
			return False
		elif float(m.group(1)) > 2 or float(m.group(1)) < 0:
			self.status_message = "Error: Vpp must be in range 0.0-2.0 V"
			return False
		elif float(m.group(3)) > 6.2e7 or float(m.group(3)) < 0:
			self.status_message = "Error: Frequency must be in range 0.0-6.2E+7 Hz"
			return False
		elif not m.group(5) in ("sine", "sqr", "tri"):
			self.status_message = "Error: Type must be either sine, sqr or tri"
			return False
		else:
			command = "/opt/redpitaya/bin/generate %d %s" % (channel, opts)
			self.conn.root.run_command(command)
			return True

	def start_continous_acquisition(self, opts):
		""" Start signal acquisition """
		""" Required: Channel Decimation """
		""" Optionals: -t to enable timestamps -s to force fsync(dataFile) """
		
		# data sanity check
		dataFileName = "/mnt/%s-data.csv" % (self.name)
		try:
			command = "/root/acquireContinousApp %s %s &" % (opts, dataFileName)
			print command
			self.conn.root.run_command(command)
		except Exception as e:
			self.app_error(e)
			return False

	def start_limited_acquisition(self, opts, timeout):
		""" Start signal acquisition """
		# data sanity check
		dataFileName = "/mnt/%s-data_CH%d.csv" % (self.name ,channel)
		try:
			command = "timeout %d /root/acquireContinous %d %s &" % (timeout, channel, opts)
			self.conn.root.run_command(command)
		except Exception as e:
			self.app_error(e)
			return False

	def acquisition_active_func(self):
		""" Get scope status. It's here, because there is no way of reading the attribute inside the server.
			(At least no documented way...) """
		try:
			command = "pgrep acquireContinous"
			self.conn.root.run_command(command)
		except Exception as e:
			self.app_error(e)
			return False
		else:
			if rstatus == "OK":
				return True
			else:
				return False

	def generator_active(self, ch):
		""" Get generator channel status. The reason of this function existece is the same as scope_active_func """
		if ch == 1:
			return not self.RP.asga.output_zero
		elif ch == 2:
			return not self.RP.asgb.output_zero


	### Interface methods -----------------------------------------------------

	def init_device(self):
		""" Start device server """
		Device.init_device(self)
		self.reconnect_tries = 0
		self.set_state_ok(DevState.INIT)
		self.board_connect()	# connect to the board

	def dev_status(self):
		""" Display appropiate status message """
		if self._state == DevState.FAULT:
			state = self._state
		else:
			state = self.get_state()
		self._status = "Device is in %s state.\n%s" % (state, self.status_message)
		self.set_status(self._status)
		return self._status

	def dev_state(self):
		""" Appropiate state handling """
		if self._state != DevState.FAULT:	# if state is FAULT set it immediately, to prevent timeouts
			# if generator or scope is active, state must be RUNNING no matter what
			if self.generator_active(1) or self.generator_active(2):
				self.set_state(DevState.RUNNING)
				return DevState.RUNNING
		self.set_state(self._state)
		return self._state

	### Attributes ------------------------------------------------------------

	@attribute(label="FPGA Temperature", dtype=float,
			   access=AttrWriteType.READ,
			   unit="*C", format="%4.3f",
			   doc="Temperature of the FPGA chip")
	def temperature(self):
		return self.RP.ams.temp

	@attribute(label="LEDs state", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_leds", unit="",
			   min_value=0, max_value=255,
			   doc="State of the LED indicators")
	def leds(self):
		return self.RP.hk.led
	def set_leds(self, leds):
		self.RP.hk.led = leds
		
	@attribute(label="PID11 setter", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_setpoint_pid11", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def setpoint_pid11(self):
		return self.RP.pid11.setpoint
	
	def set_setpoint_pid11(self, set_value):
		self.RP.pid11.setpoint = set_value
		
	@attribute(label="PID12 setter", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_setpoint_pid12", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def setpoint_pid12(self):
		return self.RP.pid12.setpoint
	
	def set_setpoint_pid12(self, set_value):
		self.RP.pid12.setpoint = set_value
		
	@attribute(label="PID21 setter", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_setpoint_pid21", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def setpoint_pid21(self):
		return self.RP.pid21.setpoint
	
	def set_setpoint_pid21(self, set_value):
		self.RP.pid21.setpoint = set_value
		
	@attribute(label="PID22 setter", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_setpoint_pid22", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def setpoint_pid22(self):
		return self.RP.pid22.setpoint
	
	def set_setpoint_pid22(self, set_value):
		self.RP.pid22.setpoint = set_value
		
	@attribute(label="PID11 proportional", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_reset_pid11", unit="",
			   min_value=0, max_value=255,
			   doc="PID reset")
	def reset_pid11(self):
		return self.RP.pid11.reset
	
	def set_reset_pid11(self, set_value):
		self.RP.pid11.reset = set_value
		
	@attribute(label="PID12 reset", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_reset_pid12", unit="",
			   min_value=0, max_value=255,
			   doc="PID reset")
	def reset_pid12(self):
		return self.RP.pid12.reset
	
	def set_reset_pid12(self, set_value):
		self.RP.pid12.reset = set_value
		
	@attribute(label="PID21 reset", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_reset_pid21", unit="",
			   min_value=0, max_value=255,
			   doc="PID reset")
	def reset_pid21(self):
		return self.RP.pid21.reset
	
	def set_reset_pid21(self, set_value):
		self.RP.pid21.reset = set_value
		
	@attribute(label="PID22 reset", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_reset_pid22", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def reset_pid22(self):
		return self.RP.pid22.reset
	
	def set_reset_pid22(self, set_value):
		self.RP.pid22.reset = set_value

	@attribute(label="PID11 proportional", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_proportional_pid11", unit="",
			   min_value=0, max_value=255,
			   doc="PID proportional")
	def proportional_pid11(self):
		return self.RP.pid11.proportional
	
	def set_proportional_pid11(self, set_value):
		self.RP.pid11.proportional = set_value
		
	@attribute(label="PID12 proportional", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_proportional_pid12", unit="",
			   min_value=0, max_value=255,
			   doc="PID proportional")
	def proportional_pid12(self):
		return self.RP.pid12.proportional
	
	def set_proportional_pid12(self, set_value):
		self.RP.pid12.proportional = set_value
		
	@attribute(label="PID21 proportional", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_proportional_pid21", unit="",
			   min_value=0, max_value=255,
			   doc="PID proportional")
	def proportional_pid21(self):
		return self.RP.pid21.proportional
	
	def set_proportional_pid21(self, set_value):
		self.RP.pid21.proportional = set_value
		
	@attribute(label="PID22 proportional", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_proportional_pid22", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def proportional_pid22(self):
		return self.RP.pid22.proportional
	
	def set_proportional_pid22(self, set_value):
		self.RP.pid22.proportional = set_value



	@attribute(label="PID11 integral", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_integral_pid11", unit="",
			   min_value=0, max_value=255,
			   doc="PID integral")
	def integral_pid11(self):
		return self.RP.pid11.integral
	
	def set_integral_pid11(self, set_value):
		self.RP.pid11.integral = set_value
		
	@attribute(label="PID12 integral", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_integral_pid12", unit="",
			   min_value=0, max_value=255,
			   doc="PID integral")
	def integral_pid12(self):
		return self.RP.pid12.integral
	
	def set_integral_pid12(self, set_value):
		self.RP.pid12.integral = set_value
		
	@attribute(label="PID21 integral", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_integral_pid21", unit="",
			   min_value=0, max_value=255,
			   doc="PID integral")
	def integral_pid21(self):
		return self.RP.pid21.integral
	
	def set_integral_pid21(self, set_value):
		self.RP.pid21.integral = set_value
		
	@attribute(label="PID22 integral", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_integral_pid22", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def integral_pid22(self):
		return self.RP.pid22.integral
	
	def set_integral_pid22(self, set_value):
		self.RP.pid22.integral = set_value

	@attribute(label="PID11 derivative", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_derivative_pid11", unit="",
			   min_value=0, max_value=255,
			   doc="PID derivative")
	def derivative_pid11(self):
		return self.RP.pid11.derivative
	
	def set_derivative_pid11(self, set_value):
		self.RP.pid11.derivative = set_value
		
	@attribute(label="PID12 derivative", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_derivative_pid12", unit="",
			   min_value=0, max_value=255,
			   doc="PID derivative")
	def derivative_pid12(self):
		return self.RP.pid12.derivative
	
	def set_derivative_pid12(self, set_value):
		self.RP.pid12.derivative = set_value
		
	@attribute(label="PID21 derivative", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_derivative_pid21", unit="",
			   min_value=0, max_value=255,
			   doc="PID derivative")
	def derivative_pid21(self):
		return self.RP.pid21.derivative
	
	def set_derivative_pid21(self, set_value):
		self.RP.pid21.derivative = set_value
		
	@attribute(label="PID22 derivative", dtype="int",		# plain int type causes errors
			   access=AttrWriteType.READ_WRITE,
			   fset="set_derivative_pid22", unit="",
			   min_value=0, max_value=255,
			   doc="PID Setpoint")
	def derivative_pid22(self):
		return self.RP.pid22.derivative
	
	def set_derivative_pid22(self, set_value):
		self.RP.pid22.derivative = set_value
	
	@attribute(label="Ping check", dtype=str,
			   access=AttrWriteType.READ,
			   doc="Connection ping check")
	def ping(self):
		try:
			self.conn.ping()
		except Exception as e:	# should be PingError, but it's not working
			self.connection_error(e)
			while(self.reconnect_tries < self.reconnect):
				self.reconnect_tries += 1
				self.board_connect()	# try to reconnect if possible

			return "FAILED"
		else:
			self.reconnect_tries = 0	# reset reconnect counter
			return "OK"

	### Generator attributes --------------------------------------------------

	@attribute(label="Generator CH1 active", dtype=bool,
			   access=AttrWriteType.READ,
			   doc="CH1 generator operation state")
	def generator_ch1_active(self):
		return self.generator_active(1)

	@attribute(label="Generator CH2 active", dtype=bool,
			   access=AttrWriteType.READ,
			   doc="CH2 generator operation state")
	def generator_ch2_active(self):
		return self.generator_active(2)


	### Generator commands ----------------------------------------------------

	@command(dtype_in=str,	# it was supposed to be an array of arguments, but since ATKPanel doesn't support that it had to change
			 doc_in="Start signal generator. Arguments: Vpp amplitude, frequency [Hz], type (sine, sqr, tri)")
	def start_generator_ch1(self, argstr):
		ch2_active = self.generator_active(2)
		if self.start_generator(1, argstr):
			if not ch2_active:				# if the other channel wasn't active earlier
				self.stop_generator(2)		# stop the other channel (required because of internal behavior)

	@command(dtype_in=str,	# it was supposed to be an array of arguments, but since ATKPanel doesn't support that it had to change
			 doc_in="Start signal generator. Arguments: Vpp amplitude, frequency [Hz], type (sine, sqr, tri)")
	def start_generator_ch2(self, argstr):
		ch1_active = self.generator_active(1)
		if self.start_generator(2, argstr):
			if not ch1_active:			# if the other channel wasn't active earlier
				self.stop_generator(1)		# stop the other channel (required because of internal behavior)

	@command(dtype_in="int", doc_in="Channel number")
	def stop_generator(self, ch):
		if ch == 1:
			self.RP.asga.output_zero = True
			self.set_state_ok(DevState.ON)
		elif ch == 2:
			self.RP.asgb.output_zero = True
			self.set_state_ok(DevState.ON)
		else:
			self.status_message = "Error: Generator channel should be 1 or 2"

	@command(dtype_in="str", doc_in="CH Decimation AbsolutePathToDataFile \
 	[Optional: -t enables timestamps -s enables fsync on data file]")
	def start_acquisition(self, argstr):
		self.start_continous_acquisition(argstr)

	@command(doc_in="Initialize PID11 with defaults")
	def initialize_pid11(self):
		return self.RP.pid11.initialize()
	
	@command(doc_in="Initialize PID12 with defaults")
	def initialize_pid12(self):
		return self.RP.pid12.initialize()
	
	@command(doc_in="Initialize PID21 with defaults")
	def initialize_pid21(self):
		return self.RP.pid21.initialize()
	
	@command(doc_in="Initialize PID22 with defaults")
	def initialize_pid22(self):
		return self.RP.pid22.initialize()
	


