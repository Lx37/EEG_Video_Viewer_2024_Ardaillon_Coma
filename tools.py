import os
import neo
import numpy as np
import scipy as sc
import ephyviewer
import pandas as pd
import datetime
import matplotlib.pyplot as plt
import quantities as pq

#

def read_EEG_syncro_trig(eeg_trc_file):
    """
    Reads EEG synchronization triggers from a .TRC file.

    Parameters:
    eeg_trc_file (str): Path to the .TRC file.

    Returns:
    np.ndarray: Array of trigger times in seconds.
    """
    seg = neo.MicromedIO(filename = eeg_trc_file).read_segment()
    ev_synchro = seg.events[1]
    ghost_trigs = []
    for ii, label in enumerate(ev_synchro.labels):
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
    """
    Calculates linear regression coefficients to project other times to EEG time space.

    Parameters:
    trig_other_times (np.ndarray): Array of trigger times from another source.
    trig_micromed_times (np.ndarray): Array of trigger times from the EEG.

    Returns:
    tuple: Coefficients (a, b) for the linear regression.
    """
    print('trigs volcan : ', np.shape(trig_other_times)[0], ' trig micromed : ', np.shape(trig_micromed_times)[0]) 
    assert np.shape(trig_other_times)[0] == np.shape(trig_micromed_times)[0], 'Not the same number of syncro trigs'
    a,b,r,tt,stderr = sc.stats.linregress(trig_other_times, trig_micromed_times)
    print('Linear regression coefficients for time projection in EEG space : a = ', a, ' b = ', b)
    
    return a, b

def rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file):
    """
    Rescales video times to EEG time space.

    Parameters:
    video_tps_file (str): Path to the .tps file containing video times.
    video_clock_file (str): Path to the .clock file containing video trigger times.
    eeg_trc_file (str): Path to the .TRC file containing EEG data.

    Returns:
    np.ndarray: Rescaled video times.
    """
    print('******* Load Video data')
    
    # Read video times from .tps file
    video_times = np.fromfile(video_tps_file, dtype= np.uint32).astype(np.float64)/1000.  # need .astype(np.float64) ?
    t0_machine = video_times[0] #TODO add description
    video_times -= t0_machine
    
    # Read synchro trig clock from .clock  
    trig_video_times = np.fromfile(video_clock_file, dtype = np.uint32).astype(np.float64)/1000.
    #print('ICI  video_clock_file data[0]: ', trig_video_times[0])
    trig_video_times -= t0_machine  # Remove the T0 from .tps file to the .clock data ! this is the T0_machine
  
    # Get coefficent to project video time to EEG time space
    trig_micromed_times = read_EEG_syncro_trig(eeg_trc_file)
    
    a, b = get_data_to_EEG_regression_coef(trig_video_times, trig_micromed_times)
    rescaled_video_time = video_times* a + b
    
    return rescaled_video_time  
    
def get_env_H5Data(env_h5_file):
    """
    Reads environmental data from an HDF5 file.

    Parameters:
    env_h5_file (str): Path to the HDF5 file.

    Returns:
    tuple: Signals, sample rate, start time, and channel names.
    """
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
    """
    Reads the header information from a file.

    Parameters:
    header_filename (str): Path to the header file.

    Returns:
    dict: Dictionary containing header information.
    """
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
    """
    Reads Volcan signal data from a raw file.

    Parameters:
    raw_filename (str): Path to the raw file.
    output (str): Output format, either 'numpy' or 'neo2'.

    Returns:
    tuple or list: Header and signals if output is 'numpy', otherwise list of AnalogSignal objects.
    """
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
    """
    Reads environmental raw data and synchronizes it with EEG data.

    Parameters:
    raw_file (str): Path to the raw file.
    eeg_trc_file (str): Path to the .TRC file containing EEG data.

    Returns:
    tuple: Raw data, raw frequency, start time, channel names, and corrected raw indices.
    """
    print('******* Load raw data')
    
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
    if patient_name in ['P03', 'P07', 'P09', 'P10', 'P11bis', 'P12', 'P15', 'P16']:
        trig_micromed_times = trig_micromed_times[:-1]
        print ("Last Micromed trig removed because not received from volcan side !")

    a, b = get_data_to_EEG_regression_coef(raw_trig, trig_micromed_times)
    print(a,b)

    corrected_raw_idx = raw_idx * a + b
    raw_freq /= a
    '''
    offset_raw_idx = sync_data_to_EEG_datetime(corrected_raw_idx, output_dirname, patient_name)
    sono_df = pd.Series(data=raw[:,0], index=offset_raw_idx)
    lux_df = pd.Series(data=raw[:,1], index=offset_raw_idx)
    '''
    channel_names = ['Sono' , 'Lux', 'Synchro']
    t_start =  corrected_raw_idx[0]
   
    #return raw[:,0:2], raw_freq, t_start, channel_names, corrected_raw_idx
    return raw, raw_freq, t_start, channel_names, corrected_raw_idx

def rescale_score_times(epoch_times, video_tps_file, video_clock_file, eeg_trc_file):
    """
    Rescales score times to EEG time space.
    Here we don't remove t0_machine as the score are linked to video frames
    just need to project it to EEG timing space
    

    Parameters:
    epoch_times (list): List of epoch times.
    video_tps_file (str): Path to the .tps file containing video times.
    video_clock_file (str): Path to the .clock file containing video trigger times.
    eeg_trc_file (str): Path to the .TRC file containing EEG data.

    Returns:
    list: Rescaled epoch times.
    """
    # Read video times from .tps file
    video_times = np.fromfile(video_tps_file, dtype= np.uint32).astype(np.float64)/1000.  # need .astype(np.float64) ?
    t0_machine = video_times[0]
    #t0_machine is not removed as the score are linked to video frames
    
    # Read synchro trig clock from .clock  
    trig_video_times = np.fromfile(video_clock_file, dtype = np.uint32).astype(np.float64)/1000.
    trig_video_times -= t0_machine  # Remove the T0 from .tps file to the .clock data ! this is the T0_machine
  
    # Get coefficent to project video time to EEG time space
    trig_micromed_times = read_EEG_syncro_trig(eeg_trc_file)

    a, b = get_data_to_EEG_regression_coef(trig_video_times, trig_micromed_times)
    rescaled_epoch_times = [a * float(x) + b for x in epoch_times]
    
    return rescaled_epoch_times  
      
def read_volcan_epoch(fac_filename, facdef_filename, video_tps_file, video_clock_file, eeg_trc_file,  output='list'):
    """
    Reads Volcan epoch data and rescales it to EEG time space.

    Parameters:
    fac_filename (str): Path to the .fac file containing epoch data.
    facdef_filename (str): Path to the .facdef file containing epoch definitions.
    video_tps_file (str): Path to the .tps file containing video times.
    video_clock_file (str): Path to the .clock file containing video trigger times.
    eeg_trc_file (str): Path to the .TRC file containing EEG data.
    output (str): Output format, either 'list', 'neo2', or 'event_epoch'.

    Returns:
    list or tuple: List of epoch arrays if output is 'list', otherwise list of Neo Epoch objects or tuple of events and epochs.
    """
    print('******* Load volcan score data')
    
    fid = open(facdef_filename,  encoding= "ISO-8859-1")
    line = fid.readline()
    epocharrays = [ ]
    while line !='':
        epocharray = { }
        epocharray['name'], n = line.replace('\'n', '').replace('\r', '').split(' ')
        epocharray['possible_labels'] = { }
        for i in range(int(n)):
            line = fid.readline().replace('\'n', '').replace('\r', '')
            code, num, key = line.split(' ')
            epocharray['possible_labels'][int(num)] = code
        epocharrays.append(epocharray)
        line = fid.readline()

    images = np.fromfile(fac_filename, dtype = np.float64).reshape(len(epocharrays)+1,-1)
    
    for i, epocharray in enumerate(epocharrays):
        epocharray['image_times'] = images[0,:]
        epocharray['image_codes'] = images[i+1,:]  # was 1 -> error, images shape is (3, 88970) for several scores
        
        # regroup image_labels in epoch with times+duration 
        fronts, = np.where( np.diff(epocharray['image_codes']) != 0 )
        fronts = np.concatenate([[0], fronts+1, [len(epocharray['image_codes']) - 1], ])
        epocharray['epoch_times'] = []
        epocharray['epoch_durations'] = []
        epocharray['epoch_labels'] = []
        #epocharray['epoch_code'] = []
        for e in range(fronts.size - 1) :
            k = epocharray['image_codes'][fronts[e]]
            if k in epocharray['possible_labels'].keys() :
                t_start = epocharray['image_times'][fronts[e]]
                t_stop = epocharray['image_times'][fronts[e+1]]
                epocharray['epoch_times'].append(t_start)
                epocharray['epoch_durations'].append(t_stop-t_start)
                epocharray['epoch_labels'].append(epocharray['possible_labels'][k])
                #epocharray['epoch_code' ].append(int(k))
                
   
    # rescale video time to EEG clock reference
    for i, epochar in enumerate(epocharrays):
        epocharrays[i]['epoch_times'] = rescale_score_times(epocharrays[i]['epoch_times'], video_tps_file, video_clock_file, eeg_trc_file)
    
    if output == 'list':
        return epocharrays
    elif output == 'neo2':
        neo_eps = [ ]
        for ep in epocharrays:
            neo_ep = neo.Epoch(name = ep['name'],   #EpochArray
                                    times = ep['epoch_times' ]*pq.s,
                                    durations = ep['epoch_durations' ]*pq.s,
                                    labels = np.array(ep['epoch_labels' ], dtype = str),
                                    )
            neo_eps.append(neo_ep)
        return neo_eps
    elif output == 'event_epoch':
        all_events = []
        all_epochs = []
        for ep in epocharrays:
            for label in ep['possible_labels'].values():
                ev_times_label = []
                epo_duration_label = []
                ev_labels = []
                for el in range (len(ep['epoch_labels'])):
                    if ep['epoch_labels'][el] == label:
                        ev_times_label.append(ep['epoch_times'][el])
                        epo_duration_label.append(ep['epoch_durations'][el])
                        ev_labels.append(label + ' num {}'.format(el))
                ev_times = np.array(ev_times_label)
                epo_duration = np.array(epo_duration_label)
                ev_labels_np = np.array(ev_labels, dtype = str)
                all_events.append({ 'time':ev_times, 'label':ev_labels_np, 'name':ep['name'] + '_' + label })
                all_epochs.append({ 'time':ev_times, 'duration':epo_duration, 'label':ev_labels_np, 'name':ep['name'] + '_' +  label })
        
        return all_events, all_epochs


def get_scores_volcan(fac_filename, facdef_filename):
    """
    Reads Volcan scores from .fac and .facdef files.

    Parameters:
    fac_filename (str): Path to the .fac file containing scores.
    facdef_filename (str): Path to the .facdef file containing score definitions.

    Returns:
    list: List of epoch arrays.
    """
    epocharrays = read_volcan_epoch(fac_filename, facdef_filename, output='list')
    #print('epocharrays : ', epocharrays)

'''    
def get_scores_volcan_h5(h5_scoreVolcan):
    
    with pd.HDFStore(h5_scoreVolcan) as hdf:
        print(hdf.keys())
    
    data_yeux = pd.read_hdf(h5_scoreVolcan,  key='/Yeux')
    print(data_yeux)
    data_yeux_np = data_yeux.to_numpy()
    print(data_yeux_np)
    
    data_motricite = pd.read_hdf(h5_scoreVolcan,  key='/Motricite')
    print(data_motricite)
    data_yeux_datetime = data_yeux.index
    print(data_motricite.index)
    data_motricite_np = data_motricite.to_numpy()
    print(data_motricite_np)
    
    mean_diff = abs(np.diff(data_yeux.index)).mean() # same datetime for both Yeux and Motricite
    sample_rate = 1 / (mean_diff.item() * 10**(-9))
    
    print('mean diff : ', mean_diff)
    print('mean diff.item() : ', mean_diff.item()) 
    print('mean diff.item() *10-9 : ', mean_diff.item() * 10**(-9))
    plt.plot(np.diff(data_yeux.index))
    
    date_start = data_yeux.index
    
    #data_yeux.plot()
    plt.show()
    
    return data_yeux_np, data_motricite_np, sample_rate, date_start
'''

    
# Test methods

def test_rescale_video_times(patient_name):
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    video_tps_file = data_raw_path + patient_name + '/' + patient_name + '_V=1.tps'
    video_clock_file =  data_raw_path + patient_name + '/' + patient_name + '.clock'
    eeg_trc_file = data_raw_path + patient_name + '/' + patient_name + '_EEG_24h.TRC'
    
    rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)

'''
def test_get_env_H5Data(patient_name):
    
    data_folder_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node'
    env_h5_file =  "{}/{}/{}_Env.h5".format(data_folder_path, patient_name, patient_name) 

    sigs, sample_rate, t_start, channel_names = get_env_H5Data(env_h5_file)
    
    print('sample_rate : ', sample_rate)
    print('t_start : , ', t_start)
''' 

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
    
def test_get_scores_volcan(patient_name):
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    video_tps_file = "{}/{}/{}_V=1.tps".format(data_raw_path, patient_name, patient_name)
    fac_filename = "{}/{}/{}_V=1.fac".format(data_raw_path, patient_name, patient_name)
    facdef_filename = "{}/{}/{}_V=1.facdef".format(data_raw_path, patient_name, patient_name)
    
    get_scores_volcan(fac_filename, facdef_filename)
    
def test_get_scores_volcan_h5(patient_name):
    
    data_folder_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/data_node'
    h5_scoreVolcan = "{}/{}/{}_ScoreVolcan.h5".format(data_folder_path, patient_name, patient_name)
    data_yeux_np, data_motricite_np, sample_rate, date_start = get_scores_volcan_h5(h5_scoreVolcan)
    
    print('sample_rate : ', sample_rate)
    print('date_start : ', date_start)
    print('date_start : ', date_start)
    
def test_read_volcan_epoch(patient_name):
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    fac_filename = "{}/{}/{}_V=1.fac".format(data_raw_path, patient_name, patient_name)
    facdef_filename = "{}/{}/{}_V=1.facdef".format(data_raw_path, patient_name, patient_name)
    
    video_tps_file = "{}/{}/{}_V=1.tps".format(data_raw_path, patient_name, patient_name)
    video_clock_file =  "{}/{}/{}.clock".format(data_raw_path, patient_name, patient_name)
    eeg_trc_file = "{}/{}/{}_EEG_24h.TRC".format(data_raw_path, patient_name, patient_name)
    
    #epocharrays = read_volcan_epoch(fac_filename, facdef_filename, output='neo2') # list neo2
    #print('epocharrays :', epocharrays)
    
    all_events, all_epochs = read_volcan_epoch(fac_filename, facdef_filename, video_tps_file, video_clock_file, eeg_trc_file, output='event_epoch')
    print('all_events :', all_events)
    print('all_epochs :', all_epochs)
 
    
if __name__ == "__main__":

    patient_name = 'P03'
    
    test_rescale_video_times(patient_name)
    #test_get_env_rawData(patient_name)
    
    #show_starts_timmings(patient_name)
   
    #test_get_scores_volcan(patient_name)
    
    #test_read_volcan_epoch(patient_name)
   
    #From data node (trying no using it - but to compare)
    #test_get_scores_volcan_h5(patient_name)
    #test_get_env_H5Data(patient_name)
    
