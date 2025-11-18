import os

def convert(convert_from, convert_to, freq=44100):
    '''convert from mp3 or wav to any other format at a specified frequency'''
    string = 'ffmpeg -i ' + '\"' + convert_from + '\"' + ' -ar ' + str(freq) + ' ' + '\"' + convert_to + '\"'
    os.system(string)

# cfrom = '/home/sligara7/Music/'
# cto = '/home/sligara7/Music/wav/'
# ff = os.listdir(cfrom)



# for k in range(len(ff)):
#     print(k)
#     cf = cfrom + ff[k]
#     ct = cto + ff[k]
#     convert(cf,ct)

cfrom = '/home/ajs7/Downloads/20240619_091515.amr'
cto = '/home/ajs7/Music/andy_song.wav'
convert(cfrom,cto)