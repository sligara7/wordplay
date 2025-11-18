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


# import os
# root = '/home/ajs7/Google Drive/mp5/midi/midi_files/'
# k = os.listdir(root)

# Xtrain = []
# ytrain = []
# for m in k:
#     print(m)
#     try:
#         X.make_notes(root + m) 
#         Xtrain.append(X.g)
#         ytrain.append(X.h)
#     except:
#         print('error msg')

# Xtrain = np.hstack((Xtrain)).T
# ytrain = np.hstack((ytrain)).T


from sklearn.multioutput import MultiOutputRegressor
from sklearn.ensemble import HistGradientBoostingRegressor

# regr = MultiOutputRegressor(HistGradientBoostingRegressor(max_iter=500, verbose=3, random_state=123)).fit(Xtrain, ytrain)

import joblib

# joblib.dump(regr, "model.pkl") 

regr = joblib.load('model.pkl')


# test = '/home/ajs7/Downloads/Comfortably_Numb_-_Pink_Floyd.mid'
test = '/home/ajs7/Downloads/Dark_Side_of_the_Moon_-_Pink_Floyd.mid'

X.make_notes(test)

Xtest = X.g
ytest = X.h

ypred = regr.predict(Xtest.T)
ytest = ytest.T

import matplotlib.pyplot as plt
plt.scatter(ypred.flatten(), ytest.flatten(), s=0.1)