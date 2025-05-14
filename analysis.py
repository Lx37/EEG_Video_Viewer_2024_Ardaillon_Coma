import mne
import platform
import neo
import numpy as np

def raw_from_neo(fname):
    
    reader = neo.MicromedIO(filename=fname)
    reader.parse_header()
    print('reader : ', reader)
    seg_micromed = reader.read_segment()
    #print('channel details: ', reader.header['signal_channels'])
    #print('event details: ', reader.header['event_channels'])
        
    anasig = seg_micromed.analogsignals[0] #only one analogsignal here
    print(anasig.shape)
    print(anasig.units)
    print(anasig.name)  # donne 'Signal' -> demander à Garcia si moyen plus clean de chopper les noms des canaux que reader.header['signal_channels']
    print(anasig.annotations)
    print(anasig.sampling_rate)
    
    # Get ecg number
    ich_ecg = 27
    if reader.header['signal_channels'][ich_ecg][0] != 'ecg+':
        print('Change ecg chan number, was ' + ich_ecg)
        return
    else:
        print('Found ECG channel : ' + str(ich_ecg))
        
    
    # import data to MNE... but.. 24h..
    
    #np_sig = anasig.rescale('mV').magnitude  # convert data to numpy array WARNING : 24h de signal = ça plante
    ecg_sig = np.transpose(anasig[:,ich_ecg].rescale('mV').magnitude)
    print('ici : ', ecg_sig.shape)
    
    sfreq = anasig.sampling_rate.magnitude
    ch_name = ['ecg+']
    info = mne.create_info(ch_name, sfreq, ch_types='ecg')
    raw = mne.io.RawArray(ecg_sig, info) # create RAW data for MNE
    
    raw.plot(block=True)
    
    
    # Old code in case    
    '''
    #ch_names = reader['signal_channels']
    #[sig.signal_channels for sig in seg_micromed.analogsignals]
    #ch_names = ch_names[0].replace('Channel bundle (', '').replace(') ','').split(',')
    #print(ch_names)
    #print(anasig.segment.channel_indexes[0].channel_names)
    for chx in reader.signal_channels:
        print(chx.index, chx.channel_names)


    # Because here we have the same on all chan
    sfreq = seg_micromed.analogsignals[0].sampling_rate
    print(sfreq)

    data = np.asarray(seg_micromed.analogsignals)
    print(np.shape(data))

    #take away first dimention of 3D segments (should be one)
    data = data[0,:,:]
    #MNE wants signals x time (instead of time x signals)
    data = np.transpose(data, (1,0))
    print(np.shape(data))
    data *= 1e-6  # putdata from microvolts to volts

    ch_list = ['EOG+', 'EOGV+', 'F3', 'Fz', 'F4', 'T3', 'C3', 'Cz', 'C4', 'T4', 'P3', 'Pz', 'P4', 'O1', 'O2']

    ## if 32 channels, only take the 15 that are similar over all subjects
    print(data)
    print(len(ch_names))
    new_ch_names = []


    new_data = np.zeros((len(ch_list), data.shape[1]))
    for ich, chname in enumerate(ch_list):
        if chname == 'EOG+':
            if chname not in ch_names:
                chname = 'heog+'
            new_idx = ch_names.index(chname)
            print('ch_names.index(chname)', ch_names.index(chname))
            new_ch_names.append(chname)
            new_data[ich,:] = data[new_idx,:]
        elif chname == 'EOGV+':
            if chname not in ch_names:
                chname = 'veog+'
            new_idx = ch_names.index(chname)
            print('ch_names.index(chname)', ch_names.index(chname))
            new_ch_names.append(chname)
            new_data[ich,:] = data[new_idx,:]
        elif chname in ch_names :
            new_idx = ch_names.index(chname)
            new_ch_names.append(chname)
            new_data[ich,:] = data[new_idx,:]


        #order = [24,25,4,5,6,8,9,10,11,12,14,15,16,18,20]
        #ch_names = [ch_names[i] for i in order]
        #data = data[order,:]
    print('new_data', new_data)

    # add stim channel
    new_ch_names.append('STI 014')
    print('new_ch_names', new_ch_names)
    logger.info('Channel names: , %s', new_ch_names)
    new_data = np.vstack((new_data, np.zeros((1, new_data.shape[1]))))

    ch_types = ['eog', 'eog'] + ['eeg' for _ in new_ch_names[2:-1]] + ['stim']
    info = mne.create_info(new_ch_names, sfreq, ch_types=ch_types)
    raw = mne.io.RawArray(new_data, info) # create RAW data for MNE

    ### LOADING EVENTS

    events = seg_micromed.events ## create a lists

    name = []
    times = []
    labels = []

    for event in seg_micromed.events:
        #print('name = ', event.name)
        name.append(event.name)
        #print('event.times.magnitude = ', event.times.magnitude)
        times.append(event.times.magnitude)
        #print('event.labels = ', event.labels)
        labels.append(event.labels)


    time = times[0] * sfreq
    columntwo = np.zeros(len(time))
    events = np.array([time.astype(int), columntwo.astype(int), labels[0].astype(int)])
    events = events.transpose()

    raw.add_events(events)
    #raw.plot(block=True)

    return raw
    '''




if __name__ == "__main__":
    
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

    raw = raw_from_neo(eeg_trc_file)

 