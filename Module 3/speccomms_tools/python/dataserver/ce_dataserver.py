#!/usr/bin/env python3
# -*- coding: utf-8 -*-


"""
CE dataserver 20v19

 -x	escenas deben comenzar y terminar con una señal para cargar/precargar controles//
	antes de comenzar el conteo
 -x formato de los datos de angulo y magnitud en 0.0 - 1.0
 -x play/loop/freeze frame/ escena

 -? variable freq using subsampling


timeline:
	.cada escena comienza enviando repetidamente el mensaje de arranque /TL07/start 1 1 1
	.luego envia el contenido del track
	.si el track por default está en modo loop, 
		se puede elegir la opción freeze para mantener una configuracion 

v1:
	no osc
	lag in load, bad threading
v2: 
	osc for both tracks
	still lag in loading
v3: 
	lfos independientes
v4:
	double OSC client
"""

# modulos
import pyxel
import argparse
import json
import math
from time import time, sleep
from oscpy.client import OSCClient
import threading

TWO_PI = 2*math.pi
old_paleton = [0, 1911635, 8267091, 34641, 
11227702, 0xAAAAAA, 12764103, 16773608, 
0xFF0007, 0xFF8700, 0xFFFF00, 0x58E000, 
0x213FFF, 0x7117FF, 16742312, 16764074]
neu_paleton = [0x1C032B, 0x002F2F, 0x193434, 0xFFFAF6, 
0x007F7F, 0xD3D000, 0xD36000, 0x59068D, 
0x005D5D, 0x9B9900, 0x984600, 0x410568, 
0x003E3E, 0x676500, 0x672E00, 0x2B0345]

# like processing's map
def pMap(value, inMin, inMax, outMin, outMax, clamp=True):
	inSpan = inMax - inMin
	outSpan = outMax - outMin
	transVal = float(value - inMin) / float(inSpan)
	outVal = outMin + (transVal * outSpan)
	if clamp:
		if outVal < outMin: outVal = outMin
		if outVal > outMax: outVal = outMax
	return outVal

threads = []

# TRACK # ----------------------------------------------------------------------------------------------- #
class Track:
	'''
		A sequence of data matrices and a sequence of metadata
		from where to extract the oscilators angles and magnitud of movement
		states:
			T0	:	empty, ready to load
			T1	:	loading
			T2	:	stoppped, ready to play
			T3	:	playing	
	'''

	def __init__(self):
		'''init track and control data'''
		self.track_data = None
		self.track_index = 0
		self.track_name = None
		self.track_dur = 0
		self.track_fn = None
		self.feats_fn = None 
		self.data = []
		self.meta = []
		self.data_len  = 0
		self.resolution = 	0
		self.t0 = 0 
		self.i = 0				# current frame index
		self.j = 0
		self.k = 0				# current phase index
		self.current_frame = None
		self.past_frame = None
		self.state = 0
		self.is_freeze = True	# 0: play, 1: freeze
		return


	def load_thread(self, track_dict):
		self.data = json.load(open(self.track_fn, 'r'))
		self.meta = json.load(open(self.metadata_fn, 'r'))
		#print("----- finished loading: ", self.track_name,": ", time())
		print("----- finished loading: ", self.track_name)
		self.data_len  = len(self.data)
		self.resolution = 24	# ! - - -- --- ---- <
		self.i = 0				# current frame index
		self.j = 0
		self.k = 0				# current phase index
		self.current_frame = self.data[self.i]
		self.is_freeze = True	# 0: loop, 1: freeze
		sleep(1)
		self.state = 2		# stopped, ready to play
		return

	def load(self, track_dict):
		'''read data for given track_metadata'''
		self.track_data = track_dict
		self.track_index = self.track_data["index"]
		self.track_name = self.track_data["name"]
		self.track_dur = self.track_data["duration"]
		self.track_fn = self.track_data["data_filename"] 
		self.metadata_fn = self.track_data["feats_filename"] 
		# loading
		self.state = 1
		self.t0 = time()
		t = threading.Thread(target = self.load_thread, args = (track_dict,))
		threads.append(t)
		t.start()
		print("----- start loading:", self.track_name,": ", self.t0)
		return

	def check_loading(self):
		return

	def update(self):
		'''
		if state==playing: choose for self.is_freeze: 
			False: play   -> next phase, then next frame
			True:  freeze -> next phase, then same frame
		'''
		if (self.state == 0):
			self.check_loading()
		elif (self.state == 1):
			self.check_loading()
			print(" ... ")
			#self.current_frame = self.past_frame
		elif (self.state == 2):
			self.current_frame = self.data[self.i]
			self.past_frame = self.current_frame
		elif (self.state == 3):
			# increase phase
			if (self.k < self.resolution):			
				self.k = self.k + 1
			else:
				if (not self.is_freeze):		# when not freezed
					# increase or reset frame index
					if (self.i < self.data_len-1): self.i = self.i + 1
					else: self.i = 0
					# update frame and reset phase			
					self.current_frame = self.data[self.i]
					self.past_frame = self.current_frame
				self.k = 0
		return

	def go_to_frame(self, whichframe = 0):
		self.k = 0
		self.i = whichframe
		self.current_frame = self.data[self.i]
		return

	def get_current_frame(self):
		""" draw current frame """
		return self.current_frame

	def get_meta(self):
		""" draw current metadata """
		return self.meta

	def get_state(self):
		"""return index, phase, resolution"""
		return [self.i, self.k, self.resolution]



# DECK # ----------------------------------------------------------------------------------------------- #
class Deck:
	'''
		An object to load, play and -mix Tracks
		states:
			D0: empty, ready to load session
			D1: stoppped, session loaded
			D2: running, state and output depends on tracks states
	'''
	def __init__(self):
		self.session_filename = "" 
		self.session = None
		self.session_name = ""
		self.session_list = ""
		#
		self.track_a_num = None
		self.track_b_num = None
		self.track_a = None
		self.track_b = None
		self.state_deck = 0
		self.is_playing = False
		return

	def load_session(self, filename="transmission.json"):
		self.session_filename = filename
		self.session = json.load(open(self.session_filename, 'r'))
		self.session_name = self.session["name"]
		self.session_list = self.session["sequence"]
		self.state_deck= 1
		self.track_a_num = 0
		self.track_b_num = 1
		return

	def start_playing(self):
		if (not self.is_playing):
			self.is_playing = True
			self.state_deck = 2
		return
	
	def stop_playing(self):
		if (self.is_playing):
			self.is_playing = False
			self.state_deck = 1
		return

	def load_track_a(self, index=0):
		if (self.state_deck >= 1):
			self.track_a_data = self.session_list[index]
			self.track_a = Track()
			self.track_a.load(self.track_a_data)
		return

	def load_track_b(self, index=1):
		if (self.state_deck >= 1):
			self.track_b_data = self.session_list[index]
			self.track_b = Track()
			self.track_b.load(self.track_b_data)
		return

	def update(self):
		'''update accoding to state_deck'''
		if (self.state_deck == 0):			#load session
			self.load_session(self.session_filename)
			self.state_deck = 1
		elif (self.state_deck == 1):		#start playing
			self.start_playing()
		elif(self.state_deck == 2):			# update tracks
			self.track_a.update()
			self.track_b.update()
		return



# App # ----------------------------------------------------------------------------------------------- #
class App:
	def __init__(self):
		pyxel.init(200, 200, fps=12, caption="[ i n t e r s p e c i f i c s ] : Speculative Communications: dataServer", palette = old_paleton)
		# argparse
		self.ap = argparse.ArgumentParser()
		self.ap.add_argument("-t", "--transmission-file",    default="transmission.json",  help="sequence of pairs of data and metadata filenames that corresponds to a track")
		self.args = vars(self.ap.parse_args())
		# --------- the deck
		self.deck = Deck()
		self.deck.load_session(self.args["transmission_file"])
		#----------osc
		self.osc_addr = "127.0.0.1"
		self.osc_port = 8000
		self.osc = OSCClient(self.osc_addr, self.osc_port)
		self.osc_addr_b = "127.0.0.1"
		self.osc_port_b = 9000
		self.osc_b = OSCClient(self.osc_addr_b, self.osc_port_b)
		# not seq but track initialized on deck
		self.index_track_a = 0
		self.index_track_b = 1
		self.deck.load_track_a(self.index_track_a)
		self.deck.load_track_b(self.index_track_b)
		#self.deck.track_a.go_to_frame(10)
		#self.deck.track_b.go_to_frame(30)
		#self.deck.track_a.is_freeze = False
		#self.deck.track_b.is_freeze = False
		#---self.deck.start_playing()
		# --------about frames
		self.current_frame = None
		self.meta = None
		self.track_state = None
		self.track_name = ""
		self.md = None
		self.c_coord = None
		self.c_cell = None
		self.c_angle = 0
		self.c_force = 0
		self.other_current_frame = None
		self.other_meta = None
		self.other_track_state = None
		self.other_track_name = None
		self.other_track_len = None
		self.other_md = None
		self.other_c_coord = None
		self.other_c_cell = None
		self.other_c_angle = 0
		self.other_c_force = 0
		# -------- about GUI
		self.which_view = 0
		self.freeze = False
		self.play = True
		self.co = 0
		self.buttons = [[1, 179, pyxel.width/2, 6],					# 0 deck A
						[pyxel.width/2, 179, pyxel.width/2-1, 6],	# 1 deck B
						[1, 186, 24, 6],							# 2 play
						[24, 186, 151, 6],							# 3 transport bar
						[175, 186, 24, 6],							# 4 stop
						[1, 193, pyxel.width-2, 6]]					# 5 space for tracks
		self.ssn = len(self.deck.session_list)
		self.segment = 198 / self.ssn
		for i in range(self.ssn):
			self.buttons.append([1+i*self.segment, 193, self.segment, 6])

		self.togb = []
		for j in range(6):
			self.togb.append([pyxel.width/2 - 5, pyxel.height/2 + 13 + j*10, 15, 10])
		self.toggle_lfos_a = [False, False, False, False, False, False]
		self.toggle_lfos_b = [False, False, False, False, False, False]

		# ----------pyxel RUN
		pyxel.run(self.update, self.draw)


	def update(self): #-----------------------------                                    #
		# get_controls
		if pyxel.btnp(pyxel.MOUSE_LEFT_BUTTON):
			clicx = pyxel.mouse_x
			clicy = pyxel.mouse_y
			# check toggle buttons
			for i in range(len(self.togb)):
				if (clicx > self.togb[i][0] and clicx < self.togb[i][0]+self.togb[i][2] and clicy > self.togb[i][1] and clicy < self.togb[i][1]+self.togb[i][3]):
					if self.which_view == 0:
						self.toggle_lfos_a[i] = not self.toggle_lfos_a[i]
					elif self.which_view == 1:
						self.toggle_lfos_b[i] = not self.toggle_lfos_b[i]
			# check deckA
			if (clicx > self.buttons[0][0] and clicx < self.buttons[0][0]+self.buttons[0][2] and clicy > self.buttons[0][1] and clicy < self.buttons[0][1]+self.buttons[0][3]):
				self.which_view = 0
			# check deckB
			if (clicx > self.buttons[1][0] and clicx < self.buttons[1][0]+self.buttons[1][2] and clicy > self.buttons[1][1] and clicy < self.buttons[1][1]+self.buttons[1][3]):
				self.which_view = 1
			# check play/stop     ---   --- also OSC
			if (clicx > self.buttons[2][0] and clicx < self.buttons[2][0]+self.buttons[2][2] and clicy > self.buttons[2][1] and clicy < self.buttons[2][1]+self.buttons[2][3]):
				if self.which_view == 0: 
					if self.deck.track_a.state == 3:
						self.deck.track_a.state = 2
						self.osc.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/STOP', [1])
						self.osc_b.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/STOP', [1])
					elif self.deck.track_a.state == 2:
						self.deck.track_a.state = 3
						self.osc.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/START', [1])
						self.osc_b.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/START', [1])
				elif self.which_view == 1: 
					if self.deck.track_b.state == 3:
						self.deck.track_b.state = 2			
						self.osc.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/STOP', [1])
						self.osc_b.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/STOP', [1])
					elif self.deck.track_b.state == 2:
						self.deck.track_b.state = 3			
						self.osc.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/START', [1])
						self.osc_b.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/START', [1])
			# check go/freeze
			if (clicx > self.buttons[4][0] and clicx < self.buttons[4][0]+self.buttons[4][2] and clicy > self.buttons[4][1] and clicy < self.buttons[4][1]+self.buttons[4][3]):
				if self.which_view == 0: self.deck.track_a.is_freeze = not self.deck.track_a.is_freeze
				elif self.which_view == 1: self.deck.track_b.is_freeze = not self.deck.track_b.is_freeze
			# check new track
			nu_track = None
			if (self.which_view == 0 and self.deck.track_a.state == 2):
				for a in range(0, self.ssn):
					if (clicx > self.buttons[6+a][0] and \
						clicx < self.buttons[6+a][0]+self.buttons[6+a][2] and \
						clicy > self.buttons[6+a][1] and \
						clicy < self.buttons[6+a][1]+self.buttons[6+a][3]):
						nu_track = a
				if not nu_track == None:
					#self.which_view = 0 if self.which_view == 1 else 1
					self.index_track_a = nu_track
					self.deck.load_track_a(self.index_track_a)
					print("\nstarted waiting")
			elif (self.which_view == 1 and self.deck.track_b.state == 2):
				for b in range(0, self.ssn):
					if (clicx > self.buttons[6+b][0] and \
						clicx < self.buttons[6+b][0]+self.buttons[6+b][2] and \
						clicy > self.buttons[6+b][1] and \
						clicy < self.buttons[6+b][1]+self.buttons[6+b][3]):
						nu_track = b
				if not nu_track == None:
					#self.which_view = 0 if self.which_view == 1 else 1
					self.index_track_b = nu_track
					self.deck.load_track_b(self.index_track_b)
					print("\nstarted waiting")

		# and get the data
		if (self.which_view==0):
			self.current_frame = self.deck.track_a.get_current_frame()
			self.meta = self.deck.track_a.get_meta()
			self.track_state = self.deck.track_a.get_state()
			self.track_name = self.deck.track_a.track_name
			self.track_len = self.deck.track_a.data_len
			self.other_current_frame = self.deck.track_b.get_current_frame()
			self.other_meta = self.deck.track_b.get_meta()
			self.other_track_state = self.deck.track_b.get_state()
			self.other_track_name = self.deck.track_b.track_name
			self.other_track_len = self.deck.track_b.data_len
		elif (self.which_view ==1):
			self.current_frame = self.deck.track_b.get_current_frame()
			self.meta = self.deck.track_b.get_meta()
			self.track_state = self.deck.track_b.get_state()
			self.track_name = self.deck.track_b.track_name
			self.track_len = self.deck.track_b.data_len
			self.other_current_frame = self.deck.track_a.get_current_frame()
			self.other_meta = self.deck.track_a.get_meta()
			self.other_track_state = self.deck.track_a.get_state()
			self.other_track_name = self.deck.track_a.track_name
			self.other_track_len = self.deck.track_a.data_len

		# and then update the deck
		self.deck.update()
		# now ready for drawing


	def draw(self): #-----------------------------                                    #
		if (self.which_view==0 and self.deck.track_a.state>=2) or (self.which_view==1 and self.deck.track_b.state>=2):
			pyxel.cls(1)
			# -MAP
			# opticflow
			for ai in range(len(self.current_frame['opticflow'])):
				ax = ai / (self.current_frame['gridHN']+4) + 2
				ay = ai % (self.current_frame['gridHN']+4) + 3
				if (len(self.current_frame['opticflow'][ai])>1):
					ang = self.current_frame['opticflow'][ai][2]/1000.0		#get angles
					mag = self.current_frame['opticflow'][ai][3]/1000.0		#get magnitudes
					coloro = int(pMap(mag, 1, 32, 8, 12))
					#print(ax, ay, ai, self.frame['opticflow'][ai])
					if coloro>=8 and coloro <=12:
						pyxel.circ(ax, ay, 1, coloro)
					else:
						pyxel.circ(ax, ay, 1, 0)
			# --- --- --- --- -GUI
			# frames
			pyxel.rectb(1, 1, pyxel.width-2, self.current_frame['gridHN']+8, 6)
			pyxel.rectb(1, self.current_frame['gridHN']+8, pyxel.width-2, 65, 6)
			# buttons
			# lfo toggles


			# decks
			cd1 = 6 if self.which_view==0 else 1
			cd2 = 1 if self.which_view==0 else 6
			pyxel.rect(self.buttons[0][0], self.buttons[0][1], self.buttons[0][2], self.buttons[0][3], cd1) # deckA
			pyxel.text(self.buttons[0][0] + self.buttons[0][2]/2-10, self.buttons[0][1]+1, "[-A-]", cd2)
			pyxel.rect(self.buttons[1][0], self.buttons[1][1], self.buttons[1][2], self.buttons[1][3], cd2) # deckB
			pyxel.text(self.buttons[1][0] + self.buttons[1][2]/2-10, self.buttons[1][1]+1, "[-B-]", cd1)
			# play / stop
			cdp1 = 1
			cdp2 = 6
			if self.which_view == 0:
				if self.deck.track_a.state == 3: 		# A-stop
					pyxel.rect(self.buttons[2][0], self.buttons[2][1], self.buttons[2][2], self.buttons[2][3], cdp2)
					pyxel.text(self.buttons[2][0] + self.buttons[2][2]/2-8, self.buttons[2][1]+1, "[>>]", cdp1)
				elif self.deck.track_a.state == 2:
					pyxel.rect(self.buttons[2][0], self.buttons[2][1], self.buttons[2][2], self.buttons[2][3], cdp1)
					pyxel.text(self.buttons[2][0] + self.buttons[2][2]/2-8, self.buttons[2][1]+1, "[--]", cdp2)
			elif self.which_view == 1:
				if self.deck.track_b.state == 3: 		# A-stop
					pyxel.rect(self.buttons[2][0], self.buttons[2][1], self.buttons[2][2], self.buttons[2][3], cdp2)
					pyxel.text(self.buttons[2][0] + self.buttons[2][2]/2-8, self.buttons[2][1]+1, "[>>]", cdp1)
				elif self.deck.track_b.state == 2:
					pyxel.rect(self.buttons[2][0], self.buttons[2][1], self.buttons[2][2], self.buttons[2][3], cdp1)
					pyxel.text(self.buttons[2][0] + self.buttons[2][2]/2-8, self.buttons[2][1]+1, "[--]", cdp2)
			# go / freeze
			if self.which_view == 0:
				if self.deck.track_a.is_freeze:
					cdp1 = 1
					cdp2 = 6
					pyxel.rect(self.buttons[4][0], self.buttons[4][1], self.buttons[4][2], self.buttons[4][3], cdp1)
					pyxel.text(self.buttons[4][0] + self.buttons[4][2]/2-8, self.buttons[4][1]+1, "[<>]", cdp2)
				else:
					cdp1 = 6
					cdp2 = 1
					pyxel.rect(self.buttons[4][0], self.buttons[4][1], self.buttons[4][2], self.buttons[4][3], cdp1)
					pyxel.text(self.buttons[4][0] + self.buttons[4][2]/2-8, self.buttons[4][1]+1, "[->]", cdp2)
			elif self.which_view == 1:
				if self.deck.track_b.is_freeze:
					cdp1 = 1
					cdp2 = 6
					pyxel.rect(self.buttons[4][0], self.buttons[4][1], self.buttons[4][2], self.buttons[4][3], cdp1)
					pyxel.text(self.buttons[4][0] + self.buttons[4][2]/2-8, self.buttons[4][1]+1, "[<>]", cdp2)
				else:
					cdp1 = 6
					cdp2 = 1
					pyxel.rect(self.buttons[4][0], self.buttons[4][1], self.buttons[4][2], self.buttons[4][3], cdp1)
					pyxel.text(self.buttons[4][0] + self.buttons[4][2]/2-8, self.buttons[4][1]+1, "[->]", cdp2)
			# transport
			cdp1 = 1
			cdp2 = 6
			i, ph, reso = self.track_state
			pyxel.rectb(self.buttons[3][0], self.buttons[3][1], self.buttons[3][2], self.buttons[3][3], cdp2) 
			pyxel.text(self.buttons[3][0] + pMap(i+ph/reso, 0, self.track_len, 0, self.buttons[3][2]-3), self.buttons[3][1] + 1, "!", cdp2)
			# tracks
			ct1 = 1 
			ct2 = 6 
			cit = self.index_track_a if self.which_view==0 else self.index_track_b
			pyxel.rectb(self.buttons[5][0], self.buttons[5][1], self.buttons[5][2], self.buttons[5][3], 6)
			for j in range(0, self.ssn):
				if j==cit:
					pyxel.rect(self.buttons[6+j][0], self.buttons[6+j][1], self.buttons[6+j][2], self.buttons[6+j][3], ct2) # track
					pyxel.text(self.buttons[6+j][0] + self.buttons[6+j][2]/2, self.buttons[6+j][1] + 1, str(j), ct1)
				else:
					pyxel.rect(self.buttons[6+j][0], self.buttons[6+j][1], self.buttons[6+j][2], self.buttons[6+j][3], ct1) # track
					pyxel.text(self.buttons[6+j][0] + self.buttons[6+j][2]/2, self.buttons[6+j][1] + 1, str(j), ct2)
			# cursor
			pyxel.circ(pyxel.mouse_x, pyxel.mouse_y, 0.2, self.co%15)
			self.co += 1

			# --- --- --- --- -features metadata
			for current_feat in range(len(self.meta)):
				self.md = self.meta[current_feat]
				i, ph, reso = self.track_state
				if (i>=self.md["init_frame"] and i<=self.md["end_frame"]):
					self.c_coord = [ int(( self.md["coordinates"][0] + self.md["radius"]*math.cos(ph*TWO_PI/reso)) / self.current_frame['gridSize']), 
									int(( self.md["coordinates"][1] + self.md["radius"]*math.sin(ph*TWO_PI/reso)) / self.current_frame['gridSize']) ]
					# rectify cell index
					if (self.c_coord[0] > self.current_frame['gridWN']): self.c_coord[0] = self.current_frame['gridWN']
					if (self.c_coord[0] < 0): self.c_coord[0] = 0
					if (self.c_coord[1] > self.current_frame['gridHN']): self.c_coord[1] = self.current_frame['gridHN']
					if (self.c_coord[1] < 0): self.c_coord[1] = 0
					# calculate cell index
					self.c_cell  = self.c_coord[1] + (self.current_frame['gridHN']+4)*self.c_coord[0]
					# get values for cell
					if (len(self.current_frame["opticflow"][self.c_cell]) > 1):
						self.c_angle = self.current_frame["opticflow"][self.c_cell][2]/1000.0  # the angle
						self.c_force = self.current_frame["opticflow"][self.c_cell][3]/1000.0  # the force
					else:
						self.c_angle = 0
						self.c_force = 0
					# draw around
					pyxel.circb(2+(self.md["coordinates"][0]-self.md["radius"])/10, 3+(self.md["coordinates"][1])/10, 0.5, 6)
					pyxel.circb(2+(self.md["coordinates"][0])/10, 3+(self.md["coordinates"][1]-self.md["radius"])/10, 0.5, 6)
					pyxel.circb(2+(self.md["coordinates"][0]+self.md["radius"])/10, 3+(self.md["coordinates"][1])/10, 0.5, 6)
					pyxel.circb(2+(self.md["coordinates"][0])/10, 3+(self.md["coordinates"][1]+self.md["radius"])/10, 0.5, 6)
					# draw center
					pyxel.circb(2+self.md["coordinates"][0]/10, 3+self.md["coordinates"][1]/10, 1, 7)
					pyxel.circb(2+self.md["coordinates"][0]/10, 3+self.md["coordinates"][1]/10, (i*reso+ph)%(self.md["radius"]/10), 5)
					pyxel.text(2+self.md["coordinates"][0]/10-5, 3+self.md["coordinates"][1]/10+5, "[" + str(self.md["index"]) + "]", 7)	
					# draw mobile
					pyxel.circ(2+self.c_coord[0], 3+self.c_coord[1], 1, (i%2)*7)
					# angle and force text				 -<--------------------- HERE JoHNNY ----------------\
					pyxel.text(pyxel.width/2 + 0, pyxel.height/2 + 17 + current_feat*10, "[" + str(self.md["index"]) + "]: " + str(self.c_angle) , 7)
					if ((self.which_view==0 and self.toggle_lfos_a[self.md["index"]]==False) or (self.which_view==1 and self.toggle_lfos_b[self.md["index"]]==False)):
						pyxel.text(pyxel.width/2 + 4, pyxel.height/2 + 17 + current_feat*10, str(self.md["index"]), 0)
					pyxel.text(pyxel.width/2 + 60, pyxel.height/2 + 17 + current_feat*10, str(self.c_force), 7)
					# angle and force bar indicators
					mag = int(pMap(self.c_angle, -180, 180, 0, 20))
					pyxel.rect(pyxel.width/2 + 20, pyxel.height/2 + 23 + current_feat*10, mag, 1, 7)
					if (self.c_force==0): coloro = 7
					else: coloro = int(pMap(self.c_force, 1, 32, 8, 12))
					if not(coloro>=8 and coloro <=12):	coloro = 0
					mag = int(pMap(self.c_force, 0, 32, 0, 20))
					pyxel.rect(pyxel.width/2 + 60, pyxel.height/2 + 23 + current_feat*10, mag, 1, coloro)
					# send OSC 
					if (self.which_view==0):
						if (self.deck.track_a.state == 3 and self.toggle_lfos_a[self.md["index"]]==True):
							self.osc.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/LFO'+str(self.md["index"]).encode(), [ph/reso*1.0, pMap(self.c_angle,-180.0, 180.0, 0.0, 1.0), self.c_force/100.0])
							self.osc_b.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/LFO'+str(self.md["index"]).encode(), [ph/reso*1.0, pMap(self.c_angle,-180.0, 180.0, 0.0, 1.0), self.c_force/100.0])
					elif (self.which_view==1):
						if ( self.deck.track_b.state == 3 and self.toggle_lfos_b[self.md["index"]]==True):
							self.osc.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/LFO'+str(self.md["index"]).encode(), [ph/reso*1.0, pMap(self.c_angle,-180.0, 180.0, 0.0, 1.0), self.c_force/100.0])
							self.osc_b.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/LFO'+str(self.md["index"]).encode(), [ph/reso*1.0, pMap(self.c_angle,-180.0, 180.0, 0.0, 1.0), self.c_force/100.0])
			
			# --- --- --- --- -other_features metadata
			for other_current_feat in range(len(self.other_meta)):
				self.other_md = self.other_meta[other_current_feat]
				ii, phph, resoreso = self.other_track_state
				if (ii>=self.other_md["init_frame"] and i<=self.other_md["end_frame"]):
					self.other_c_coord = [ int(( self.other_md["coordinates"][0] + self.other_md["radius"]*math.cos(ph*TWO_PI/reso)) / self.other_current_frame['gridSize']), 
											int(( self.other_md["coordinates"][1] + self.other_md["radius"]*math.sin(ph*TWO_PI/reso)) / self.other_current_frame['gridSize']) ]
					# rectify cell index
					if (self.other_c_coord[0] > self.other_current_frame['gridWN']): self.other_c_coord[0] = self.other_current_frame['gridWN']
					if (self.other_c_coord[0] < 0): self.other_c_coord[0] = 0
					if (self.other_c_coord[1] > self.other_current_frame['gridHN']): self.other_c_coord[1] = self.current_frame['gridHN']
					if (self.other_c_coord[1] < 0): self.other_c_coord[1] = 0
					# calculate cell index
					self.other_c_cell  = self.other_c_coord[1] + (self.other_current_frame['gridHN']+4)*self.other_c_coord[0]
					# get values for cell
					if (len(self.other_current_frame["opticflow"][self.other_c_cell]) > 1):
						self.other_c_angle = self.other_current_frame["opticflow"][self.other_c_cell][2]/1000.0  # the angle
						self.other_c_force = self.other_current_frame["opticflow"][self.other_c_cell][3]/1000.0  # the force
					else:
						self.other_c_angle = 0
						self.other_c_force = 0
					# send more OSC 
					if (self.which_view==0):
						if (self.deck.track_b.state == 3 and self.toggle_lfos_b[self.other_md["index"]]==True):
							self.osc.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/LFO'+str(self.other_md["index"]).encode(), [phph/resoreso*1.0, pMap(self.other_c_angle,-180.0, 180.0, 0.0, 1.0), self.other_c_force/100.0])
							self.osc_b.send_message(b'/CE/'+self.deck.track_b.track_name.encode()+b'/LFO'+str(self.other_md["index"]).encode(), [phph/resoreso*1.0, pMap(self.other_c_angle,-180.0, 180.0, 0.0, 1.0), self.other_c_force/100.0])
					elif (self.which_view==1):
						if (self.deck.track_a.state == 3 and self.toggle_lfos_a[self.other_md["index"]]==True):
							self.osc.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/LFO'+str(self.other_md["index"]).encode(), [phph/resoreso*1.0, pMap(self.other_c_angle,-180.0, 180.0, 0.0, 1.0), self.other_c_force/100.0])
							self.osc_b.send_message(b'/CE/'+self.deck.track_a.track_name.encode()+b'/LFO'+str(self.other_md["index"]).encode(), [phph/resoreso*1.0, pMap(self.other_c_angle,-180.0, 180.0, 0.0, 1.0), self.other_c_force/100.0])


			# --- --- --- --- -current track info
			pyxel.text(pyxel.width/2 -90, pyxel.height/2 + 57, "Speculative       +", 7)	
			pyxel.text(pyxel.width/2 -90, pyxel.height/2 + 67, "+    Communications", 7)	
			pyxel.text(pyxel.width/2 -90, pyxel.height/2 + 17, "[session]: "+self.deck.session_name, 7)	
			pyxel.text(pyxel.width/2 -90, pyxel.height/2 + 27, "[track]:   " + self.track_name, 7)	
			pyxel.text(pyxel.width/2 -90, pyxel.height/2 + 37, "[t]:     " + str(i) + "." + str(ph) + "/" + str(self.track_len), 7)
		elif(self.deck.track_a.state<=1 or self.deck.track_b.state<=1):
			# cursor
			pyxel.circ(pyxel.mouse_x, pyxel.mouse_y, 0.2, self.co%15)
			self.co += 1



# ----------------------------------------------------------------------------------------------- #
# ----------------------------------------------------------------------------------------------- #
App()

