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
        self.midi_link = midi_link
        self.init_parse()
        for k in self.msg:
            for j in self.msg[k]:
                self.msg[k][j] = self.velocity_dict(self.msg[k][j])
    
            
# X = mmp()
#X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/CdL.mid')
# X.parse('/home/ajs7/Google Drive/mp5/midi/midi_files/Shout_-_Tears_For_Fears_-.mid')
# i = X.inst
# m = X.msg
# s = X.song_length