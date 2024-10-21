
import neo
from ephyviewer import mkQApp, MainViewer, TraceViewer, get_sources_from_neo_rawio
from ephyviewer import EpochEncoder, compose_mainviewer_from_sources, VideoViewer, CsvEpochSource
from ephyviewer.tests.testing_tools import make_fake_video_source
from ephyviewer import video
import numpy as np
import datetime
import platform

from tools import rescale_video_times

print('Working on computer : ', platform.uname().node)

if platform.uname().node == 'tkz-XPS': #'tkz-XPS' pc portable Alex
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    data_node_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node/'

#TODO get platform.uname().node for Hugo

patient_name = 'P03'
print('Working on patient : ', patient_name)
data_raw_path = data_raw_path + patient_name + '/'

# Get raw data : EEG and Video
eeg_trc_file = data_raw_path + patient_name + '_EEG_24h.TRC'
video_avi_file = data_raw_path + patient_name + '_V=1.avi'
video_tps_file = data_raw_path + patient_name + '_V=1.tps'
video_clock_file =  data_raw_path + patient_name + '.clock'

video_times = np.fromfile(video_tps_file, dtype= np.uint32)/1000.
video_times -= video_times[0]
#print('video_times from video recording : ', video_times)
#print('ici : ############################################')
#print('shape video_times : ', np.shape(video_times))

# rescale video time to EEG time, using trig clock
rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
#To be removed when rescaled_viedo_tiles will work
video_times = np.fromfile(video_tps_file, dtype= np.uint32)/1000.  # need .astype(np.float64) ?
video_times -= video_times[0]
#print('video_times from video recording : ', video_times)
#print('shape video_times : ', np.shape(video_times))



#neo_seg = neo.MicromedIO(filename = eeg_trc_file).read_segment()
# print(neo_seg.analogsignals)
# print(neo_seg.analogsignals[0])
# print(neo_seg.analogsignals[0].shape)
# print(neo_seg.analogsignals[0].units)
#print('neo_seg.rec_datetime : ', neo_seg.rec_datetime)
#print('neo_seg.annotations : ', neo_seg.annotations)
# print(neo_seg.magnitude)
#recdatetime

# Load EEG signals
neorawio = neo.MicromedIO(filename = eeg_trc_file) 
sources = get_sources_from_neo_rawio(neorawio)
print('sources from neo_rawio : ', sources)

# General app window
app = mkQApp()
#win = MainViewer(datetime0 = neo_seg.rec_datetime, show_label_datetime=True)
win = MainViewer(datetime0 = neorawio.read_segment().rec_datetime, show_label_datetime=True)


# EEG viewer
mainviewer = compose_mainviewer_from_sources(sources, mainviewer=win) #TODO rewrite it better

# Video viewer rescaled_video_time
#video_source = video.MultiVideoFileSource([video_avi_file], [video_times]) #TODO rescale video_times to EEG
video_source = video.MultiVideoFileSource([video_avi_file], [rescaled_video_time]) #TODO rescale video_times to EEG
video_view = VideoViewer(source=video_source, name='video')
win.add_view(video_view)

# Environement viewer (sono + lux)

#sono_source =  
#sono_view = TraceViewer(source=sono_source, name='sonometre')
#mainviewer.add_view(sono_view)

# Epoch encoder
# lets encode some dev mood along the day
'''
possible_labels = ['euphoric', 'nervous', 'hungry',  'triumphant']
filename = 'example_dev_mood_encoder.csv'
source_epoch = CsvEpochSource(filename, possible_labels)
encoder_view = EpochEncoder(source=source_epoch, name='Encoder')
win.add_view(encoder_view)
'''


#Run
win.show()
app.exec()