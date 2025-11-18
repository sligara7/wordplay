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

# r0, j0, a0 = X.dotop(d[:,1])

# r = X.reco(r0, j0, a0)

# q = 10
# xlen = X.xlen
# ind = np.argsort(a0, axis=0)[-q:,:]
# r10 = np.take_along_axis(r0, ind, axis=0)
# j10 = np.take_along_axis(j0, ind, axis=0)
# f10 = X.freq[ind]


# x = np.zeros(xlen*r10.shape[1])
# xinc = np.arange(0,x.shape[0],xlen)
# xinc = np.tile(xinc, [q,1])

# unifreq = np.unique(ind)


# for k in unifreq:
#     f = X.freq[k]
#     c = np.cos(2*np.pi*f*np.arange(xlen)/sf)
#     s = np.sin(2*np.pi*f*np.arange(xlen)/sf)
#     y = np.argwhere(ind==k)

#     for m,n in y:
#         xcoord0 = xinc[m,n]
#         xcoord1 = xcoord0 + xlen
#         x[xcoord0:xcoord1] = x[xcoord0:xcoord1] + c * r10[m,n] + s * j10[m,n]
        

# mx = np.max(np.abs(x))
# x = x / mx * 32767

write('/home/ajs7/Music/andy_song_reco.wav', sf, np.vstack((q,q)).T)



