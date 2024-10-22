
import neo
from ephyviewer import mkQApp, MainViewer, TraceViewer, get_sources_from_neo_rawio
from ephyviewer import EpochEncoder, compose_mainviewer_from_sources, VideoViewer, CsvEpochSource
from ephyviewer.tests.testing_tools import make_fake_video_source
from ephyviewer import video
import numpy as np
import datetime
import platform
#import pandas as pd

from tools import rescale_video_times, get_env_data

print('Working on computer : ', platform.uname().node)

if platform.uname().node == 'tkz-XPS': #'tkz-XPS' pc portable Alex
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    data_node_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node/'
#TODO get platform.uname().node for Hugo

patient_name = 'P03'
print('Working on patient : ', patient_name)
#data_raw_path = data_raw_path + patient_name + '/'
#data_node_path = data_node_path + patient_name + '/'

# Get raw data : EEG and Video
#eeg_trc_file = data_raw_path + patient_name + '_EEG_24h.TRC'
#video_avi_file = data_raw_path + patient_name + '_V=1.avi'
#video_tps_file = data_raw_path + patient_name + '_V=1.tps'
#video_clock_file =  data_raw_path + patient_name + '.clock'

eeg_trc_file = "{}/{}/{}_EEG_24h.TRC".format(data_raw_path, patient_name, patient_name)
video_avi_file = "{}/{}/{}_V=1.avi".format(data_raw_path, patient_name, patient_name)
video_tps_file = "{}/{}/{}_V=1.tps".format(data_raw_path, patient_name, patient_name)
video_clock_file = "{}/{}/{}.clock".format(data_raw_path, patient_name, patient_name)

rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)

# Get sono and lux from data node (already rescaled)
env_h5_file =  "{}/{}/{}_Env.h5".format(data_node_path, patient_name, patient_name) 

#video_times = np.fromfile(video_tps_file, dtype= np.uint32)/1000.
#video_times -= video_times[0]

#print('video_times from video recording : ', video_times)
#print('ici : ############################################')
#print('shape video_times : ', np.shape(video_times))

# rescale video time to EEG time, using trig clock
#rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
#To be removed when rescaled_viedo_tiles will work
#video_times = np.fromfile(video_tps_file, dtype= np.uint32)/1000.  # need .astype(np.float64) ?
#video_times -= video_times[0]
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
datetime0 = neorawio.read_segment().rec_datetime

# General app window
app = mkQApp()
#win = MainViewer(datetime0 = neo_seg.rec_datetime, show_label_datetime=True)
win = MainViewer(datetime0 = datetime0, show_label_datetime=True)


# EEG viewer
mainviewer = compose_mainviewer_from_sources(sources, mainviewer=win) #TODO rewrite it better

# Video viewer rescaled_video_time
#video_source = video.MultiVideoFileSource([video_avi_file], [video_times]) #TODO rescale video_times to EEG
video_source = video.MultiVideoFileSource([video_avi_file], [rescaled_video_time]) 
video_view = VideoViewer(source=video_source, name='video')
win.add_view(video_view)

# Environement viewer (sono + lux)
env_sigs, env_sample_rate, env_t_start, channel_names = get_env_data(env_h5_file)


print(type(env_sigs[0]))
print('datetime0 : ', datetime0)
print('type(datetime0) : ', type(datetime0))
print('env_t_start : ', env_t_start)
print('type(env_t_start) : ', type(env_t_start))

rescaled_t_start = (env_t_start - datetime0).total_seconds()
print('rescaled_t_start : ', rescaled_t_start)
print('type rescaled_t_start : ', type(rescaled_t_start))

#sono_view = TraceViewer(source=env_sources, name='environment')
sono_view = TraceViewer.from_numpy(env_sigs, env_sample_rate, rescaled_t_start, 'Environment', channel_names)
mainviewer.add_view(sono_view)

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