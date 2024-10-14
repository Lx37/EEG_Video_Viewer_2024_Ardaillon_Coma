
import neo
from ephyviewer import mkQApp, MainViewer, TraceViewer, get_sources_from_neo_rawio
from ephyviewer import EpochEncoder, compose_mainviewer_from_sources, VideoViewer, CsvEpochSource
from ephyviewer.tests.testing_tools import make_fake_video_source
from ephyviewer import video
import numpy as np
import datetime

data_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/P03_EEG_24h.TRC'
video_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/P03_V=1.avi'
video_tps= '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/P03_V=1.tps'

video_times = np.fromfile(video_tps, dtype= np.uint32)/1000.
video_times -= video_times[0]
print('video_times : ', video_times)

neo_seg = neo.MicromedIO(filename = data_path).read_segment()
# print(neo_seg.analogsignals)
# print(neo_seg.analogsignals[0])
# print(neo_seg.analogsignals[0].shape)
# print(neo_seg.analogsignals[0].units)
print('neo_seg.rec_datetime : ', neo_seg.rec_datetime)
print('neo_seg.annotations : ', neo_seg.annotations)
# print(neo_seg.magnitude)
#recdatetime

# Load EEG signals
neorawio = neo.MicromedIO(filename = data_path) 
sources = get_sources_from_neo_rawio(neorawio)
print('sources from neo_rawio : ', sources)

# General app window
app = mkQApp()
win = MainViewer(datetime0 = neo_seg.rec_datetime, show_label_datetime=True)

# EEG viewer
mainviewer = compose_mainviewer_from_sources(sources, mainviewer=win)

# Video viewer
video_source = video.MultiVideoFileSource([video_path], [video_times]) #TODO rewrite it better
video_view = VideoViewer(source=video_source, name='video')
win.add_view(video_view)

# Epoch encoder
# lets encode some dev mood along the day
possible_labels = ['euphoric', 'nervous', 'hungry',  'triumphant']
filename = 'example_dev_mood_encoder.csv'
source_epoch = CsvEpochSource(filename, possible_labels)
encoder_view = EpochEncoder(source=source_epoch, name='Encoder')
win.add_view(encoder_view)


#Run
win.show()
app.exec()