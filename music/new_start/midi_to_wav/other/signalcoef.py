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
        


# Test code commented out to allow import without errors
# from scipy.io.wavfile import read

# # sf, d = read('/home/ajs7/Downloads/music/cg2/60_mcg_mf_080.wav')
# #sf, d = read('/home/ajs7/Music/CdL.wav')
# sf, d = read('/home/ajs7/Music/andy_song.wav')
# X = coef(samplefreq=sf)

# r0 = X.dotop(d)
# median_noise = np.median(r0)
# avg_noise = np.mean(r0)
# std_noise = np.std(r0)

# r1 = r0.copy()
# r1[r1<median_noise+2*std_noise] = 0

# # r1 = X.dotop(d[:,1])

# import matplotlib.pyplot as plt
# plt.imshow(r1, aspect='auto')

# # x = np.arange(0, 7, 1/44100)

# # q = np.sin(np.pi*2*27.5*8*x)
# # q[q>0] = q[q>0] * 32767
# # q[q<0] = q[q<0] * 32768

# # r = X.dotop(q)
# # f = X.f

