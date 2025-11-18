import numpy as np
import os
from scipy.io.wavfile import read
from decaytable2 import table

class signal():
    
    def __init__(self, note_offset=21, samplefreq=44100,
                 tmx=32767, tmn=-32768,
                 standard_A4=440.0, 
                 note_sec=10.0,
                 tm=1/25,
                 max_vel=127):
        
        self.note_A0 = standard_A4 / 16
        self.tmx = tmx
        self.tmn = tmn
        self.sf = samplefreq
        self.x = np.arange(0,note_sec,1/samplefreq)
        self.note_offset = note_offset
        self.stm = np.int64(samplefreq * tm)
        x = np.arange(self.stm)
        self.trunk = -x / self.stm + 1
        self.trunk = np.vstack((self.trunk,self.trunk)).T
        self.mxv = max_vel
        self.midi_inst1()
        self.tab = table

    def note_freqs(self, note_idx):
        '''returns frequency of note; input index of not
        e based on piano with 
        88 keys, with A4=440.  note_A0 is typically the lowest note on a 
        standard piano (index=0).  Any index above or below would also be computed'''
        return self.note_A0 * 2 ** (note_idx / 12) 
    
    def signal(self, n, v):
        strvel, ratio = self.find_vel(v)
        filename = self.m[(n, strvel)]
        sf, d = read(self.piano_link + filename)
        #consider checking the sf - if not same as class, do interpolation
        #https://numpy.org/doc/stable/reference/generated/numpy.interp.html
        self.mxy = d.shape[0]
        return d * ratio
    
    def midi_inst1(self, link='/home/ajs7/Downloads/music/cg2/'):
        r = np.linspace(0,127,7)
        self.r = r[2:]
        self.s = {self.r[0]:'p', 
                  self.r[1]:'mp',
                  self.r[2]:'mf',
                  self.r[3]:'f',
                  self.r[4]:'ff'}
        
        self.piano_link = link
        self.m = {}
        for k in os.listdir(link):
            string = k.split('_')
            if string[1] == 'mcg':
                note = int(string[-1].split('.')[0]) - self.note_offset
                self.m[(note,string[2])] = k

    def find_vel(self, v):
        d = np.argmin(np.abs(self.r - v))
        ratio = v / self.r[d]
        return self.s[self.r[d]], ratio
    
    def shape_note(self, y, i0, i1, i2):
        instrument = self.tab[self.midi_instrument + 1]
        if instrument[2]:
            t = i2 - i0
        else:
            t = i1 - i0
        if t > self.stm:
            z = y.copy()
            if z.shape[0] >= t:
                z = z[:t, :]
            z[-self.stm:, :] = z[-self.stm:, :] * self.trunk
            return z, i0 + z.shape[0]
        else:
            return np.array([0.0, 0.0]), 1
        
    def rtn_note(self, inst, note, vel):
        self.midi_instrument = inst
        piano_volume, ratio = self.find_vel(vel)
        filename = self.m[(note, piano_volume)]
        sf, y = read(self.piano_link + filename)
        y = y * ratio
        return y
    
    def scale(self, song):
        rmn = np.min(song)
        rmx = np.max(song)
        if rmx > self.tmx or rmn < self.tmn:
            if rmx >= np.abs(rmn):
                song = song / rmx * self.tmx
            else:
                song = song / rmn * self.tmn
        return song.astype('int16')