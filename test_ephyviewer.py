
import neo
from ephyviewer import mkQApp, MainViewer, TraceViewer, get_sources_from_neo_rawio, compose_mainviewer_from_sources, VideoViewer
from  ephyviewer.tests.testing_tools import make_fake_video_source
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

neorawio = neo.MicromedIO(filename = data_path) 

sources = get_sources_from_neo_rawio(neorawio)
print('sources from neo_rawio : ', sources)

app = mkQApp()
win = MainViewer(datetime0 = neo_seg.rec_datetime, show_label_datetime=True)

mainviewer = compose_mainviewer_from_sources(sources, mainviewer=win)

video_source = video.MultiVideoFileSource([video_path], [video_times])

video_view = VideoViewer(source=video_source, name='video')
win.add_view(video_view)

#view1 = TraceViewer.from_neo_analogsignal(neo_seg.analogsignals, 'sigs')
#win.add_view(view1)


# fake sigs
# sigs = np.random.rand(100000,16)
# sample_rate = 1000.
# t_start = 0.

# #Create the main window that can contain several viewers
# win = MainViewer()
# view1 = TraceViewer.from_numpy(sigs, sample_rate, t_start, 'Signals')
# win.add_view(view1)

# #Parameters can be set in script
# view1.params['scale_mode'] = 'same_for_all'
# view1.params['display_labels'] = True
# And also parameters for each channel
# view1.by_channel_params['ch0', 'visible'] = False
# view1.by_channel_params['ch15', 'color'] = '#FF00AA'

# #Run
win.show()
app.exec()