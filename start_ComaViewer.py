
import neo
from ephyviewer import mkQApp, MainViewer, TraceViewer, get_sources_from_neo_rawio, EpochViewer, EventList
from ephyviewer import EpochEncoder, compose_mainviewer_from_sources, VideoViewer, CsvEpochSource
from ephyviewer.tests.testing_tools import make_fake_video_source
from ephyviewer import video
from ephyviewer import InMemoryEventSource, InMemoryEpochSource
import numpy as np
import datetime
import platform
#import pandas as pd

from tools import rescale_video_times, get_env_rawData, read_volcan_epoch #get_env_H5Data

print('Working on computer : ', platform.uname().node)

if platform.uname().node == 'tkz-XPS': #'tkz-XPS' pc portable Alex
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    data_node_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node/'
#si chez Hugo ou ailleurs :
else:
    data_raw_path = '/Users/arda/Desktop/Python/coma_ardaillon_raw/'
    #data_node_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node/'

patient_name = 'P03'
print('Working on patient : ', patient_name)

eeg_trc_file = "{}/{}/{}_EEG_24h.TRC".format(data_raw_path, patient_name, patient_name)
video_avi_file = "{}/{}/{}_V=1.avi".format(data_raw_path, patient_name, patient_name)
video_tps_file = "{}/{}/{}_V=1.tps".format(data_raw_path, patient_name, patient_name)
video_clock_file = "{}/{}/{}.clock".format(data_raw_path, patient_name, patient_name)
fac_filename = "{}/{}/{}_V=1.fac".format(data_raw_path, patient_name, patient_name)
facdef_filename = "{}/{}/{}_V=1.facdef".format(data_raw_path, patient_name, patient_name)
raw_file =  "{}/{}/{}.raw".format(data_raw_path, patient_name, patient_name)

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

# Environement viewer (sono + lux)
env_sigs, env_sample_rate, env_t_start, channel_names, corrected_raw_idx = get_env_rawData(raw_file, eeg_trc_file)
sono_view = TraceViewer.from_numpy(env_sigs, env_sample_rate, env_t_start, 'Environment', channel_names)
mainviewer.add_view(sono_view)

# Video viewer rescaled_video_time
rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
video_source = video.MultiVideoFileSource([video_avi_file], [rescaled_video_time])# [rescaled_video_time]) 
video_view = VideoViewer(source=video_source, name='video')
win.add_view(video_view)


# Epoch viewer for Florent scores 
all_events, all_epochs = read_volcan_epoch(fac_filename, facdef_filename, video_tps_file, video_clock_file, eeg_trc_file, output='event_epoch') #list  neo2
source_ev = InMemoryEventSource(all_events=all_events)
source_ep = InMemoryEpochSource(all_epochs=all_epochs)
epoch_view = EpochViewer(source=source_ep, name='epoch Volcan Florent')
event_view = EventList(source=source_ev, name='event')
#epo_view.by_channel_params['ch0', 'color'] = '#AA00AA'
#epo_view.params['xsize'] = 6.5

win.add_view(epoch_view)
win.add_view(event_view)
##################


# Epoch encoder lets encode some dev mood along the day
possible_labels = ['euphoric', 'nervous', 'hungry',  'triumphant']
filename = 'example_dev_mood_encoder.csv'
source_epoch = CsvEpochSource(filename, possible_labels)
encoder_view = EpochEncoder(source=source_epoch, name='Encoder')
win.add_view(encoder_view)



#Run
win.show()
app.exec()