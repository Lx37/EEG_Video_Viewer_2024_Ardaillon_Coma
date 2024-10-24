import os
import neo
import numpy as np
import scipy as sc
import ephyviewer
import pandas as pd
import datetime

def read_EEG_syncro_trig(eeg_trc_file):
    seg = neo.MicromedIO(filename = eeg_trc_file).read_segment()
    #print('seg : ', seg)
    #print('seg.events : ', seg.events)
    #for ev in seg.events:
    #    #print('   ', ev.name, ev.times, ev.labels)
    #    print('ev.labels ###################"   ', ev.labels)
    #ev_synchro = seg.eventarrays[1]
    ev_synchro = seg.events[1]
    ghost_trigs = []
    for ii, label in enumerate(ev_synchro.labels):
        #print 'trig ', ii, ' label ', label
        if label.find('Trigger') == -1:
            ghost_trigs.append(ii)
            print('found a ghost trigg at pos ' + str(ii) + ' label is : ' + label + ' !')
    if 'P05' in eeg_trc_file:
        ghost_trigs.append(539)  # manualy found..
    if 'P010' in eeg_trc_file:
        ghost_trigs.append(32)  # manualy found..
    if 'P11bis' in eeg_trc_file:
        ghost_trigs.append([8,9])  # manualy found..
    if 'P17' in eeg_trc_file:
        ghost_trigs.append(668)  # manualy found..
    trig_micromed_times = np.delete(ev_synchro.times.rescale('s').magnitude, ghost_trigs)
    return trig_micromed_times

def get_data_to_EEG_regression_coef(trig_other_times, trig_micromed_times):
    
    print('trigs volcan : ', np.shape(trig_other_times)[0], ' trig micromed : ', np.shape(trig_micromed_times)[0]) 
    assert np.shape(trig_other_times)[0] == np.shape(trig_micromed_times)[0], 'Not the same number of syncro trigs'
    a,b,r,tt,stderr = sc.stats.linregress(trig_other_times, trig_micromed_times)
    # print trig_other_times[0]
    # print trig_micromed_times[0]
    print("a : ", a)
    print("b : ", b)
    return a, b

def rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file):
    
    # Read video times from .tps file
    video_times = np.fromfile(video_tps_file, dtype= np.uint32).astype(np.float64)/1000.  # need .astype(np.float64) ?
    video_times -= video_times[0]
    print('video_times from video recording : ', video_times[0])
    print('shape video_times : ', np.shape(video_times))
    
    # Read synchro trig clock from .clock  
    trig_video_times = np.fromfile(video_clock_file, dtype = np.uint32).astype(np.float64)/1000.
    trig_video_times -= trig_video_times[0]
    #print('trig_video_times from video clock file : ', trig_video_times)
    #print('shape trig_video_times : ', np.shape(trig_video_times))
    
    # Get coefficent to project video time to EEG time space
    trig_micromed_times = read_EEG_syncro_trig(eeg_trc_file)
    
    '''
    if patient_name in ['P03', 'P07', 'P09', 'P10', 'P11bis', 'P12', 'P15', 'P16']:
    trig_micromed_times = trig_micromed_times[:-1]
    print "Last Micromed trig removed because not received from volcan side !"
    '''
    
    a, b = get_data_to_EEG_regression_coef(trig_video_times, trig_micromed_times)
    rescaled_video_time = video_times* a + b
    
    #data_s*pow(10,9) ?
    #rescaled_video_time + record_time ?*
    
    print('Rescaled_video_time  : ', rescaled_video_time[0])
    print('shape rescaled_video_time : ', np.shape(rescaled_video_time))
    
    #diff_rescaled_notrescaled = rescaled_video_time - video_times
    #print('diff_rescaled_notrescaled : ', diff_rescaled_notrescaled)
    
    return rescaled_video_time

    
    
def get_env_H5Data(env_h5_file):
    
    #list keys
    #with pd.HDFStore(data_path) as hdf:
    #    print(hdf.keys())
    
    lux_signal = pd.read_hdf(env_h5_file,  key='/lux')
    sono_signal = pd.read_hdf(env_h5_file,  key='/sono')
    
    #assert(lux_signal.index.all() == sono_signal.index.all())
    
    print('np.shape(lux_signal.to_numpy()) : ',  np.shape(lux_signal.to_numpy()))

    sigs = np.stack((lux_signal.to_numpy(), sono_signal.to_numpy()), axis=1)
    print('np.shape(sigs) : ',  np.shape(sigs))
    channel_names = ['Lux' , 'Sono'] #{0: Lux, 1: peaks1}
    
    mean_diff = abs(np.diff(lux_signal.index)).mean()
    sample_rate = 1 / (mean_diff.item() * 10**(-9))
   
    t_start = pd.to_datetime(lux_signal.index[0])#/ 10**9#.item() # * 10**(-9)
    #print('t_start : ', t_start)
    #print('t_start type : ', type(t_start))

    #env_sources = ephyviewer.InMemoryAnalogSignalSource(signals, sample_rate, t_start)
    
    return sigs, sample_rate, t_start, channel_names
    
    
def read_header(header_filename):
    #~ print header_filename
    d = { }
    for line in open(header_filename):
        k,v = line.replace('\n', '').replace('\r', '').split(':')
        d[k] = v
    if 'frequence' in d:
        d['frequence'] = float(d['frequence'])
    if 'dtype' in d:
        d['dtype'] = np.dtype(d['dtype'])
    if 'nbvoies' in d:
        d['nbvoies'] = int(d['nbvoies'])
        channelnames = [ ]
        for i in range(d['nbvoies']):
            channelnames.append(d['nom'+str(i+1)])
        d['channelnames'] = channelnames

    return d    

def read_volcan_signal(raw_filename, output = 'neo2'):
    header_filename = os.path.splitext(raw_filename)[0]+'.header'
    d = read_header(header_filename)
    sigs = np.fromfile(raw_filename, dtype = d['dtype'],).reshape(-1, d['nbvoies'])
    
    if output == 'numpy':
        return d, sigs
    if output == 'neo2':
        anasigs = [ ]
        for i, name in enumerate(d['channelnames']):
            anasigs.append(neo.AnalogSignal(sigs[:,i]*pq.V, t_start = 0.*pq.s,
                        sampling_rate = d['frequence']*pq.Hz, name = name))
        return anasigs

def get_env_rawData(raw_file, eeg_trc_file):
    header, raw = read_volcan_signal(raw_file,output='numpy')
    
    raw_freq = header['frequence']
    raw_idx = np.arange(0,raw.shape[0]/raw_freq,1./raw_freq)
    raw_trig = raw_idx[np.where( (raw[1:,2]>1) & (raw[:-1,2]<1) )]

    truc = np.where(np.ediff1d(raw_trig)<119)
    print ("pos where diff between volcan trig are < 119 :", truc, " value : ",  np.ediff1d(raw_trig)[truc])
    print (len(raw_trig))
    
    trig_micromed_times = read_EEG_syncro_trig(eeg_trc_file)

    truc = np.where(np.ediff1d(trig_micromed_times)<119)
    print ("pos where diff betwenn micromed trig are < 119 :",  truc, " value : ",  np.ediff1d(trig_micromed_times)[truc])
    print (len(trig_micromed_times))

    patient_name = eeg_trc_file.split('/')[-1][0:3]
    print('patient_name : ', patient_name)
    if patient_name in ['P03', 'P07', 'P09', 'P10', 'P11bis', 'P12', 'P15', 'P16']:
        trig_micromed_times = trig_micromed_times[:-1]
        print ("Last Micromed trig removed because not received from volcan side !")

    a, b = get_data_to_EEG_regression_coef(raw_trig, trig_micromed_times)
    print(a,b)

    corrected_raw_idx = raw_idx * a + b

    '''
    offset_raw_idx = sync_data_to_EEG_datetime(corrected_raw_idx, output_dirname, patient_name)
    sono_df = pd.Series(data=raw[:,0], index=offset_raw_idx)
    lux_df = pd.Series(data=raw[:,1], index=offset_raw_idx)
    '''
    channel_names = ['Sono' , 'Lux']
    t_start =  corrected_raw_idx[0]
    print('t_start env data : ', t_start)

    return raw[:,0:2], raw_freq, t_start, channel_names, corrected_raw_idx
    
    
    
# Test methods

def test_rescale_video_times(patient_name):
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    video_tps_file = data_raw_path + patient_name + '/' + patient_name + '_V=1.tps'
    video_clock_file =  data_raw_path + patient_name + '/' + patient_name + '.clock'
    eeg_trc_file = data_raw_path + patient_name + '/' + patient_name + '_EEG_24h.TRC'
    
    rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
    
def test_get_env_rawData(patient_name):
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    raw_file =  "{}/{}/{}.raw".format(data_raw_path, patient_name, patient_name)
    eeg_trc_file = "{}/{}/{}_EEG_24h.TRC".format(data_raw_path, patient_name, patient_name)
    
    raw, raw_freq, t_start, channel_names, corrected_raw_idx = get_env_rawData(raw_file, eeg_trc_file)
    print('raw_freq : ', raw_freq)
    print('t_start : ', t_start)
    print('raw : ', raw)
    print('raw shape : ', np.shape(raw))
    
def show_starts_timmings(patient_name):
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    video_tps_file = data_raw_path + patient_name + '/' + patient_name + '_V=1.tps'
    video_clock_file =  data_raw_path + patient_name + '/' + patient_name + '.clock'
    eeg_trc_file = data_raw_path + patient_name + '/' + patient_name + '_EEG_24h.TRC'
    raw_file =  "{}/{}/{}.raw".format(data_raw_path, patient_name, patient_name)
    
    rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
    raw, raw_freq, t_start, channel_names, corrected_raw_idx = get_env_rawData(raw_file, eeg_trc_file)
    
    neorawio = neo.MicromedIO(filename = eeg_trc_file) 
    EEG_rec_datetime = neorawio.read_segment().rec_datetime
    
    print('EEG_rec_datetime : ', EEG_rec_datetime)
    time_delta_env = datetime.timedelta(seconds=corrected_raw_idx[0])
    print('Env (sono/lux) start : ', EEG_rec_datetime + time_delta_env)
    print('time_delta_env : ', time_delta_env)
    time_delta_video = datetime.timedelta(seconds=rescaled_video_time[0])
    print('Video start : ', EEG_rec_datetime + time_delta_video)
    print('time_delta_video : ', time_delta_video)
    
    
if __name__ == "__main__":

    patient_name = 'P03'
    
    #test_rescale_video_times(patient_name)
    #test_get_env_rawData(patient_name)
    
    show_starts_timmings(patient_name)