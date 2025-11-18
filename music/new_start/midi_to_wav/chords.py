#chords - https://www.edmprod.com/different-chord-types/

import musefx as mf
import numpy as np
import matplotlib.pyplot as plt

#create freq
standard_a4 = 440.0
freq,note_index,octaves,note_names = mf.notes(standard_a4)

#define sample freq (sf); most typical is 44100 samples / second
sf = 44100

#define scaling factor to data to a "common volume"
scaling_factor = 5000

#create properly sampled data table of all notes
tab2 = np.array(mf.notetable2(freq, 1, sf)) * scaling_factor
tab44 = np.array(mf.notetable(freq, 1 / (standard_a4 / 16), sf))

#create list for all data
data = []
#major chord - A major chord consists of a root note (1st), a major third (+4 semitones), and a perfect 5th (+7 semitones).
majorchord = []
for ii in range(0, len(freq)-7):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:]
    majorchord.append(d)
majorchord = np.array(majorchord)
majorchord = majorchord.flatten()
majorchord = majorchord + majorchord * (0+1j)  
majorchord = np.abs(np.array(mf.wave_array(tab44, majorchord)))
data.append(majorchord)
#plt.imshow(majorchord.T)

#minor chord - A minor chord consists of a root note (1st), a minor third (+3 semitones), and a perfect 5th (+7 semitones).
minorchord = []
for ii in range(0, len(freq)-7):
    d = tab2[ii,:] + tab2[ii+3,:] + tab2[ii+7,:]
    minorchord.append(d)
minorchord = np.array(minorchord)
minorchord = minorchord.flatten()
minorchord = minorchord + minorchord * (0+1j)  
minorchord = np.abs(np.array(mf.wave_array(tab44, minorchord)))
data.append(minorchord)
#plt.imshow(minorchord.T)

#diminished chord consists of a root note (1st), a minor third (+3 semitones), and a diminished/flat fifth (+6 semitones).
dimchord = []
for ii in range(0, len(freq)-6):
    d = tab2[ii,:] + tab2[ii+3,:] + tab2[ii+6,:]
    dimchord.append(d)
dimchord = np.array(dimchord)
dimchord = dimchord.flatten()
dimchord = dimchord + dimchord * (0+1j)  
dimchord = np.abs(np.array(mf.wave_array(tab44, dimchord)))
data.append(dimchord)
#plt.imshow(dimchord.T)

#Major Seventh Chord - consists of a root note (1st), a major third (+4 semitones), a perfect 5th (+7 semitones), and a major 7th (+11 semitones)
maj7chord = []
for ii in range(0, len(freq)-11):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:] + tab2[ii+11,:]
    maj7chord.append(d)
maj7chord = np.array(maj7chord)
maj7chord = maj7chord.flatten()
maj7chord = maj7chord + maj7chord * (0+1j)  
maj7chord = np.abs(np.array(mf.wave_array(tab44, maj7chord)))
data.append(maj7chord)
#plt.imshow(maj7chord.T)

#Minor Seventh - consists of a root note (1st), a minor third (+3 semitones), a perfect 5th (+7 semitones), and a minor 7th (+10 semitones).
min7chord = []
for ii in range(0, len(freq)-10):
    d = tab2[ii,:] + tab2[ii+3,:] + tab2[ii+7,:] + tab2[ii+10,:]
    min7chord.append(d)
min7chord = np.array(min7chord)
min7chord = min7chord.flatten()
min7chord = min7chord + min7chord * (0+1j)  
min7chord = np.abs(np.array(mf.wave_array(tab44, min7chord)))
data.append(min7chord)
#plt.imshow(min7chord.T)

#Dominant Seventh - consists of a root note (1st), a major third (+4 semitones), a perfect 5th (+7 semitones), and a minor 7th (+10 semitones).
dom7chord = []
for ii in range(0, len(freq)-10):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:] + tab2[ii+10,:]
    dom7chord.append(d)
dom7chord = np.array(dom7chord)
dom7chord = dom7chord.flatten()
dom7chord = dom7chord + dom7chord * (0+1j)  
dom7chord = np.abs(np.array(mf.wave_array(tab44, dom7chord)))
data.append(dom7chord)
#plt.imshow(dom7chord.T)

#sus2 chord consists of a root note (1st), a major second (+2 semitones), and a perfect fifth (+7 semitones). 
sus2chord = []
for ii in range(0, len(freq)-7):
    d = tab2[ii,:] + tab2[ii+2,:] + tab2[ii+7,:]
    sus2chord.append(d)
sus2chord = np.array(sus2chord)
sus2chord = sus2chord.flatten()
sus2chord = sus2chord + sus2chord * (0+1j)  
sus2chord = np.abs(np.array(mf.wave_array(tab44, sus2chord)))
data.append(sus2chord)
#plt.imshow(sus2chord.T)

#sus4 chord consists of a root note (1st), a major fourth (+5 semitones), and a perfect fifth (+7 semitones). 
sus4chord = []
for ii in range(0, len(freq)-7):
    d = tab2[ii,:] + tab2[ii+5,:] + tab2[ii+7,:]
    sus4chord.append(d)
sus4chord = np.array(sus4chord)
sus4chord = sus4chord.flatten()
sus4chord = sus4chord + sus4chord * (0+1j)  
sus4chord = np.abs(np.array(mf.wave_array(tab44, sus4chord)))
data.append(sus4chord)
#plt.imshow(sus4chord.T)

#Augmented Chords - consists of a root note (1st), a major third (+4 semitones), and an augmented 5th (+8 semitones). 
augchord = []
for ii in range(0, len(freq)-8):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+8,:]
    augchord.append(d)
augchord = np.array(augchord)
augchord = augchord.flatten()
augchord = augchord + augchord * (0+1j)  
augchord = np.abs(np.array(mf.wave_array(tab44, augchord)))
data.append(augchord)
#plt.imshow(augchord.T)

#dominant ninth nine chord consists of a root, major 3rd (+4 semitones), perfect 5th (+ 7 semitones), minor/flat 7th (+10 semitones), and major 9th (+14 semitones).
dom9chord = []
for ii in range(0, len(freq)-14):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:] + tab2[ii+10,:] + tab2[ii+14,:]
    dom9chord.append(d)
dom9chord = np.array(dom9chord)
dom9chord = dom9chord.flatten()
dom9chord = dom9chord + dom9chord * (0+1j)  
dom9chord = np.abs(np.array(mf.wave_array(tab44, dom9chord)))
data.append(dom9chord)
#plt.imshow(augchord.T)

#major eleventh chord consists of a root note (1st), a major third (+4 semitones), a perfect 5th (+7 semitones), a major 7th (+11 semitones), a major 9th (+14 semitones), and an 11th (+17 semitones).
maj11chord = []
for ii in range(0, len(freq)-17):
    d = tab2[ii,:] + tab2[ii+4,:] + tab2[ii+7,:] + tab2[ii+11,:] + tab2[ii+14,:] + tab2[ii+17,:]
    maj11chord.append(d)
maj11chord = np.array(maj11chord)
maj11chord = maj11chord.flatten()
maj11chord = maj11chord + maj11chord * (0+1j)  
maj11chord = np.abs(np.array(mf.wave_array(tab44, maj11chord)))
data.append(maj11chord)
#plt.imshow(maj11chord.T)
