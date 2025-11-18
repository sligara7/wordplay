import numpy as np

def note_freqs(note_idx, standard_A4): 
    note_A0 = standard_A4 / 16
    return note_A0 * 2 ** (note_idx / 12) 

def freqs(keys, note_start, standard_A4):
    k = np.arange(note_start, keys)
    f = note_freqs(k, standard_A4)
    return f

# def rotate(l, n): 
#     return l[n:] + l[:n]

def returnlist(octave, keys, note_start):
    octo = octave * (keys // 12)
    modulo = octave[:keys % 12]
    octo = octo + modulo
    if note_start > 0:
        octo = octo[note_start:]
    elif note_start < 0:
        prior = np.abs(note_start) // 12
        modulo = np.abs(note_start) % 12
        begoct = octave * prior + octave[-modulo:]
        octo = begoct + octo
    return octo

def trueoctaves(octo, keys, note_start):
    k = np.arange(note_start, keys) // 12
    octo = np.array(octo) + k
    return octo

def notes(standard_A4=440.0,
          keys=88,
          note_start=0,
          octaves=[0,0,0,1,1,1,1,1,1,1,1,1], 
          sharp_names=['A','A#','B','C','C#','D','D#','E','F','F#','G','G#'],
          flat_names=['A','Bb','B','C','Db','D','Eb','E','F','Gb','G','Ab'],
          ):
    
    allsharp = returnlist(sharp_names, keys, note_start)
    allflat = returnlist(flat_names, keys, note_start)
    alloct = returnlist(octaves, keys, note_start)
    alloct = trueoctaves(alloct, keys, note_start)
    allfreq = freqs(keys, note_start, standard_A4)
    allindex = np.arange(note_start, keys)
    
    for k in range(len(allsharp)):
        mstr = allsharp[k] + str(alloct[k])
        nstr = allflat[k] + str(alloct[k])
        print(mstr, nstr, allindex[k], allfreq[k])
        
notes()
