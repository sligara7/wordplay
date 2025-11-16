import numpy as np
from scipy.io.wavfile import write
from signalcoef import coef
from parse_class3 import mmp
from signal_class import signal


class make_instrument():
    def __init__(self, note_offset=21, samplefreq=44100, perc_chan_0=9, perc_chan_1=16,
                 tmx=32767, tmn=-32768,
                 standard_A4=440.0, 
                 note_sec=10.0,
                 tm=1/25,
                 max_vel=127,
                 cycles=4,
                 increments=12,
                 standard_keys=88,
                 ):
        
        self.mmp = mmp(note_offset, perc_chan_0, perc_chan_1)
        
        self.standard_keys = standard_keys
        
        self.signal = signal(note_offset, samplefreq,
                     tmx, tmn,
                     standard_A4, 
                     note_sec,
                     tm,
                     max_vel)
        
        self.Y0 = coef(samplefreq, 
                       cycles, 
                       standard_A4, 
                       note_begin=0, 
                       note_end=standard_keys, 
                       increments=1)
            
        self.Y1 = coef(samplefreq, 
                       cycles, 
                       standard_A4, 
                       note_begin=-1, 
                       note_end=standard_keys+1, 
                       increments=increments)

    def place_notes(self, channel, note):
        for vel in self.mmp.msg[channel][note]:
            y = self.signal.rtn_note(self.mmp.inst[channel], note, vel)
            for times in self.mmp.msg[channel][note][vel]:
                i0 = round(times[0] * self.signal.sf)
                i1 = round(times[1] * self.signal.sf)
                i2 = round(times[2] * self.signal.sf)
                z, b = self.signal.shape_note(y, i0, i1, i2)
                self.song[i0:b, :] = self.song[i0:b, :] + z
                p = divmod(i0, self.Y0.xlen)
                q = divmod(b, self.Y0.xlen)
                p0 = p[0]
                #p1 = 1 - (p[1] / self.Y0.xlen)
                q0 = q[0] 
                #q1 = q[1] / self.Y0.xlen

                self.dummy[note,p0:q0] = 1.0
                # self.dummy[note,p0] = p1
                # self.dummy[note,q0] = q1
    
    def make_notes(self, midi_link):
        #how do I want to adjust for max/min notes in a song??
        self.mmp.parse(midi_link)
        song_length = int(self.signal.sf * self.mmp.song_length) + 1
        self.song = np.zeros([song_length,2]).astype('float64')
        self.dummy = self.Y0.stacksig(self.song[:,0])[:self.standard_keys,:]
        for channel in self.mmp.msg:
            if channel==self.mmp.pc0 or channel==self.mmp.pc1:
                pass
            else:
                for note in self.mmp.msg[channel]:
                    self.place_notes(channel, note)
        self.song = self.signal.scale(self.song) 
        
        h = []
        g = []
        for k in range(self.song.shape[1]):
            h.append(self.Y0.dotop(self.song[:,k]))
            g.append(self.Y1.dotop(self.song[:,k]))
        self.h = np.max(np.stack((h)), axis=0)
        self.h = self.h * self.dummy
        self.g = np.max(np.stack((g)), axis=0)
        
X = make_instrument()

import numpy as np


class coef:
    
    def __init__(self, 
                 samplefreq=44100, 
                 cycles=4, 
                 standard_A4=440.0, 
                 note_begin=-1, #consider staring at -1 
                 note_end=89, #consider changing to 89
                 increments=12): #consider increments of 12
        
        self.sf = samplefreq
        self.A0 = standard_A4 / 16
        self.length = cycles / self.A0
        self.nb = note_begin
        self.ne = note_end
        self.inc = increments
        self.table()
        self.xlen = self.c.shape[1]
    
    def note_freqs(self, note_idx):
        return self.A0 * 2 ** (note_idx / 12) 

    def note_index(self):
        h = np.arange(self.nb, self.ne, 1/self.inc)
        f = []
        for k in h:
            f.append(self.note_freqs(k))
        self.f = np.array(f)

    def xinc(self):
        return np.arange(0, self.length, 1/self.sf)

    def table(self):
        x = self.xinc()
        self.note_index()
        s = []
        c = []
        for k in self.f:
            s.append(np.sin(np.pi*2*k*x))    
            c.append(np.cos(np.pi*2*k*x))
        self.c = np.array(c)
        self.s = np.array(s)

    def stacksig(self, s):
        q = divmod(s.shape[0], self.xlen)
        if q[1] != 0:
            r = np.zeros(self.xlen - q[1])
            z = np.hstack((s,r))
            return np.reshape(z, [self.xlen, -1], order='F')
        else:
            return np.reshape(s, [self.xlen, -1], order='F')
    
    def dotop(self, signal):
        q = self.stacksig(signal.astype(dtype=np.float64))
        r = np.dot(self.c, q) * 2 / self.xlen
        j = np.dot(self.s, q) * 2 / self.xlen
        return np.sqrt(np.square(r) + np.square(j))
        


from scipy.io.wavfile import read

# sf, d = read('/home/ajs7/Downloads/music/cg2/60_mcg_mf_080.wav')
#sf, d = read('/home/ajs7/Music/CdL.wav')
sf, d = read('/home/ajs7/Music/andy_song.wav')
X = coef(samplefreq=sf)

r0 = X.dotop(d)
median_noise = np.median(r0)
avg_noise = np.mean(r0)
std_noise = np.std(r0)

r1 = r0.copy()
r1[r1<median_noise+2*std_noise] = 0

# r1 = X.dotop(d[:,1])

import matplotlib.pyplot as plt
plt.imshow(r1, aspect='auto')

# x = np.arange(0, 7, 1/44100)

# q = np.sin(np.pi*2*27.5*8*x)
# q[q>0] = q[q>0] * 32767
# q[q<0] = q[q<0] * 32768

# r = X.dotop(q)
# f = X.f

import mido

class mmp:
    '''midi message parse - decypher midi messages into a dictionary
    https://mido.readthedocs.io/en/stable/files/midi.html
    '''
    
    def __init__(self, note_offset=21, perc_chan_0=9, perc_chan_1=16, **kw):
        self.pc0 = perc_chan_0
        self.pc1 = perc_chan_1
        self.note_offset = note_offset

    def init_parse(self):
        mid = mido.MidiFile(self.midi_link)
        self.msg = {}
        self.inst = {}
        total_time = 0.0
        for k in mid:
            total_time = total_time + k.time
            if k.type == 'note_on':
                if k.channel == self.pc0 or k.channel == self.pc1:
                    offset = k.note 
                else:
                    offset = k.note-self.note_offset
                    if offset > self.note_max:
                        self.note_max = offset
                    if offset < self.note_min:
                        self.note_min = offset
            
                if k.channel in self.msg:
                    if offset in self.msg[k.channel]:
                        self.msg[k.channel][offset].append([k.velocity, total_time])
                    else:
                        self.msg[k.channel][offset] = [[k.velocity, total_time]]
                else:
                    self.msg[k.channel] = {offset:[[k.velocity, total_time]]} 
                        
            elif k.type == 'program_change': 
                self.inst[k.channel] = k.program
                
            self.song_length = total_time
            
    def velocity_dict(self, q):
        if len(q) % 2 == 0:
            n = {}
            for k in range(0,len(q),2):
                vel = q[k][0]
                i0 = q[k][1]
                i1 = q[k+1][1]
                if len(q) - k > 2:
                    avail = q[k+2][1]
                else:
                    avail = self.song_length
                #use velocity as key
                #use list of [begin time, end time, available time] as entry 
                if vel in n:
                    n[vel].append([i0, i1, avail])
                else:
                    n[vel] = [[i0, i1, avail]]
                
        elif len(q) == 1:
            n = {}
            vel = q[0][0]
            i0 = q[0][0]
            i1 = q[0][0]
            n[vel] = [[i0, i1, self.song_length]]
            
        else:
            #consider refining this
            n = {}
            n[0] = [[0.0, 0.0, 0.0]]
            
        return n
            
    def parse(self, midi_link):
        self.note_max=0
        self.note_min=127
        self.midi_link = midi_link
        self.init_parse()
        for k in self.msg:
            for j in self.msg[k]:
                self.msg[k][j] = self.velocity_dict(self.msg[k][j])
    
            
#X = mmp()
# X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/CdL.mid')
# X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/Shout_-_Tears_For_Fears_-.mid')
#X.parse('G:\My Drive\mp5\midi\midi_files\Shout_-_Tears_For_Fears_-.mid')
# i = X.inst
#m = X.msg
# s = X.song_length

import mido

class mmp:
    '''midi message parse - decypher midi messages into a dictionary
    https://mido.readthedocs.io/en/stable/files/midi.html
    '''
    
    def __init__(self, note_offset=21, perc_chan_0=9, perc_chan_1=16, **kw):
        self.pc0 = perc_chan_0
        self.pc1 = perc_chan_1
        self.note_offset = note_offset

    def init_parse(self):
        mid = mido.MidiFile(self.midi_link)
        self.msg = {}
        self.inst = {}
        total_time = 0.0
        for k in mid:
            total_time = total_time + k.time
            if k.type == 'note_on':
                if k.channel == self.pc0 or k.channel == self.pc1:
                    offset = k.note 
                else:
                    offset = k.note-self.note_offset
                    if offset > self.note_max:
                        self.note_max = offset
                    if offset < self.note_min:
                        self.note_min = offset
            
                if k.channel in self.msg:
                    if offset in self.msg[k.channel]:
                        self.msg[k.channel][offset].append([k.velocity, total_time])
                    else:
                        self.msg[k.channel][offset] = [[k.velocity, total_time]]
                else:
                    self.msg[k.channel] = {offset:[[k.velocity, total_time]]} 
                        
            elif k.type == 'program_change': 
                self.inst[k.channel] = k.program
                
            self.song_length = total_time
            
    def velocity_dict(self, q):
        if len(q) % 2 == 0:
            n = {}
            for k in range(0,len(q),2):
                vel = q[k][0]
                i0 = q[k][1]
                i1 = q[k+1][1]
                if len(q) - k > 2:
                    avail = q[k+2][1]
                else:
                    avail = self.song_length
                #use velocity as key
                #use list of [begin time, end time, available time] as entry 
                if vel in n:
                    n[vel].append([i0, i1, avail])
                else:
                    n[vel] = [[i0, i1, avail]]
                
        elif len(q) == 1:
            n = {}
            vel = q[0][0]
            i0 = q[0][0]
            i1 = q[0][0]
            n[vel] = [[i0, i1, self.song_length]]
            
        else:
            #consider refining this
            n = {}
            n[0] = [[0.0, 0.0, 0.0]]
            
        return n
            
    def parse(self, midi_link):
        self.note_max=0
        self.note_min=127
        self.midi_link = midi_link
        self.init_parse()
        for k in self.msg:
            for j in self.msg[k]:
                self.msg[k][j] = self.velocity_dict(self.msg[k][j])
    
            
#X = mmp()
# X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/CdL.mid')
# X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/Shout_-_Tears_For_Fears_-.mid')
#X.parse('G:\My Drive\mp5\midi\midi_files\Shout_-_Tears_For_Fears_-.mid')
# i = X.inst
#m = X.msg
# s = X.song_length

# https://en.wikipedia.org/wiki/General_MIDI_Level_2
'''returns dictionary:
            name of instrument (string value),
            does instrument decay (True / False),
            does is decay interupted (True / False) '''

table = {1: ['acounstic grand piano', True, True], 
                    2: ['bright acoustic piano', True, True],
                    3: ['electric grand piano', False, True],
                    4: ['honky-tonk piano', True, True],
                    5: ['electric piano 1', False, True],
                    6: ['electric piano 2', False, True],
                    7: ['harpsichord', True, True],
                    8: ['clavinet', False, True],
                    9: ['celesta', True, True],
                    10: ['glockenspiel', True, True],
                    11: ['music box', True, True],
                    12: ['Vibraphones', True, True],
                    13: ['Marimbas', True, True],
                    14: ['Xylophones', True, True],
                    15: ['Tubular Bells', True, True],
                    16: ['Dulcimer/Santur', True, True],
                    17: ['Drawbar Organ 1', False, True],
                    18: ['Percussive B3 Organ 1', False, True],
                    19: ['Rock Organ', False, True],
                    20: ['Church Organ 1', False, True],
                    21: ['Reed Organ', False, True],
                    22: ['French Accordion', False, False],
                    23: ['Harmonica', False, False],
                    24: ['Bandoneon', False, False],
                    25: ['Nylon-Strings Guitar 1', False, False],
                    26: ['Steel-Strings Guitar', False, False],
                    27: ['Jazz Guitar', False, False],
                    28: ['Clean Electric Guitar', True, False],
                    29: ['Muted Electric Guitar', False, False],
                    30: ['Overdriven Guitar', False, False],
                    31: ['Distortion Guitar', False, False],
                    32: ['Guitar Harmonics', True, False],
                    33: ['Acoustic Bass', True, False],
                    34: ['Fingered Bass', True, False],
                    35: ['Picked Bass', True, False],
                    36: ['Fretless Bass', True, False],
                    37: ['Slapped Bass 1', True, False],
                    38: ['Slapped Bass 2', True, False],
                    39: ['Synth-Bass 1', False, True],
                    40: ['Synth-Bass 2', False, True],
                    41: ['Violin', False, False],
                    42: ['Viola', False, False],
                    43: ['Cello', False, False],
                    44: ['Contrabass', False, False],
                    45: ['Tremelo', False, False],
                    46: ['Pizzicato', True, False],
                    47: ['Harp', True, True],
                    48: ['Timpani', True, False],
                    49: ['Strings Ensemble 1', False, False],
                    50: ['Strings Ensemble 2', False, False],
                    51: ['Synth-Strings 1', False, False],
                    52: ['Synth-Strings 2', False, False],
                    53: ['Choir Aahs 1', False, False],
                    54: ['Voice Oohs', False, False],
                    55: ['Synth-Voices', False, False],
                    56: ['Orchestral Hits', False, False],
                    57: ['Trumpet', False, False],
                    58: ['Trombone 1', False, False],
                    59: ['Tuba', False, False],
                    60: ['Muted Trumpet 1', False, False],
                    61: ['French Horns 1', False, False],
                    62: ['Brass Section 1', False, False],
                    63: ['Synth-Brass 1', False, False],
                    64: ['Synth-Brass 2', False, False],
                    65: ['Soprano Saxophone', False, False],
                    66: ['Alto Saxophone', False, False],
                    67: ['Tenor Saxophone', False, False],
                    68: ['Baritone Saxophone', False, False],
                    69: ['Oboe', False, False],
                    70: ['English Horn', False, False],
                    71: ['Bassoon', False, False],
                    72: ['Clarinet', False, False],
                    73: ['Piccolo', False, False],
                    74: ['Flute', False, False],
                    75: ['Recorder', False, False],
                    76: ['Pan Flutes', False, False],
                    77: ['Bottles Blown Flutes', False, False],
                    78: ['Shakuhachi', False, False],
                    79: ['Whistle', False, False],
                    80: ['Ocarina', False, False],
                    81: ['Square Lead', False, False],
                    82: ['Saw Lead', False, False],
                    83: ['Synth Calliope', False, False],
                    84: ['Chiffer Lead', False, False],
                    85: ['Charang', True, False],
                    86: ['Solo Synth Vox', False, False],
                    87: ['5th Saw Wave', False, False],
                    88: ['Bass & Lead', True, False],
                    89: ['Fantasia Pad', True, True],
                    90: ['Warm Pad', True, True],
                    91: ['made up', False, False],
                    92: ['made up', False, False],
                    93: ['made up', False, False],
                    94: ['made up', False, False],
                    95: ['made up', False, False],
                    96: ['made up', False, False],
                    97: ['made up', False, False],
                    98: ['made up', False, False],
                    99: ['made up', False, False],
                    100: ['made up', False, False],
                    101: ['made up', False, False],
                    102: ['made up', False, False],
                    103: ['made up', False, False],
                    104: ['made up', False, False],
                    105: ['made up', False, False],
                    106: ['made up', False, False],
                    107: ['made up', False, False],
                    108: ['made up', False, False],
                    109: ['made up', False, False],
                    110: ['made up', False, False],
                    111: ['made up', False, False],
                    112: ['made up', False, False],
                    113: ['made up', False, False],
                    114: ['made up', False, False],
                    115: ['made up', False, False],
                    116: ['made up', False, False],
                    117: ['made up', False, False],
                    118: ['made up', False, False],
                    119: ['made up', False, False],
                    120: ['made up', False, False],
                    121: ['made up', False, False],
                    122: ['made up', False, False],
                    123: ['made up', False, False],
                    124: ['made up', False, False],
                    125: ['made up', False, False],
                    126: ['made up', False, False],
                    127: ['made up', False, False]}

import numpy as np


class coef:
    
    def __init__(self, 
                 samplefreq=44100, 
                 cycles=4, 
                 standard_A4=440.0, 
                 note_begin=-1, 
                 note_end=89, 
                 increments=12):
        
        self.sf = samplefreq
        self.A0 = standard_A4 / 16
        self.length = cycles / self.A0
        self.nb = note_begin
        self.ne = note_end
        self.inc = increments
        self.table()
        self.xlen = self.c.shape[1]
    
    def note_freqs(self, note_idx):
        return self.A0 * 2 ** (note_idx / 12) 

    def note_index(self):
        h = np.arange(self.nb, self.ne, 1/self.inc)
        f = []
        for k in h:
            f.append(self.note_freqs(k))
        self.freq = np.array(f)

    def xinc(self):
        return np.arange(0, self.length, 1/self.sf)

    def table(self):
        x = self.xinc()
        self.note_index()
        s = []
        c = []
        for k in self.freq:
            s.append(np.sin(np.pi*2*k*x))    
            c.append(np.cos(np.pi*2*k*x))
        self.c = np.array(c)
        self.s = np.array(s)

    def stacksig(self, s):
        q = divmod(s.shape[0], self.xlen)
        if q[1] != 0:
            r = np.zeros(self.xlen - q[1])
            z = np.hstack((s,r))
            return np.reshape(z, [self.xlen, -1], order='F')
        else:
            return np.reshape(s, [self.xlen, -1], order='F')
    
    def dotop(self, signal):
        q = self.stacksig(signal.astype(dtype=np.float64))
        r = np.dot(self.c, q) * 2 / self.xlen
        j = np.dot(self.s, q) * 2 / self.xlen
        return r, j, np.sqrt(np.square(r) + np.square(j))
        

    def reco(self, r0, j0, a0, q=50):
    
        xlen = self.xlen
        ind = np.argsort(a0, axis=0)[-q:,:]
        r10 = np.take_along_axis(r0, ind, axis=0)
        j10 = np.take_along_axis(j0, ind, axis=0)
        f10 = self.freq[ind]

        x = np.zeros(xlen*r10.shape[1])
        xinc = np.arange(0,x.shape[0],xlen)
        xinc = np.tile(xinc, [q,1])

        unifreq = np.unique(ind)

        for k in unifreq:
            f = X.freq[k]
            c = np.cos(2*np.pi*f*np.arange(xlen)/sf)
            s = np.sin(2*np.pi*f*np.arange(xlen)/sf)
            y = np.argwhere(ind==k)

            for m,n in y:
                xcoord0 = xinc[m,n]
                xcoord1 = xcoord0 + xlen
                x[xcoord0:xcoord1] = x[xcoord0:xcoord1] + c * r10[m,n] + s * j10[m,n]
                

        mx = np.max(np.abs(x))
        
        if mx>32767:    
            x = x / mx * 32767
            
        return x.astype(np.int16)

from scipy.io.wavfile import read, write

sf, d = read('/home/ajs7/Music/andy_song.wav')
X = coef(samplefreq=sf)
freq = X.freq

r0, j0, a0 = X.dotop(d)

q = X.reco(r0, j0, a0)