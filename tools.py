import os
import neo
import numpy as np
import scipy as sc


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
    video_times = np.fromfile(video_tps_file, dtype= np.uint32)/1000.  # need .astype(np.float64) ?
    video_times -= video_times[0]
    print('video_times from video recording : ', video_times)
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
    
    print('Rescaled_video_time  : ', rescaled_video_time)
    print('shape rescaled_video_time : ', np.shape(rescaled_video_time))
    #print('shape video_times : ', np.shape(video_times))
    
    diff_rescaled_notrescaled = rescaled_video_time - video_times
    print('diff_rescaled_notrescaled : ', diff_rescaled_notrescaled)
    
    return rescaled_video_time

    
    
# Test methods

def test_rescale_video_times():
    
    data_raw_path = '/home/tkz/Projets/data/data_Florent_Hugo_2024/raw/'
    patient_name = 'P03'
    video_tps_file = data_raw_path + patient_name + '/' + patient_name + '_V=1.tps'
    video_clock_file =  data_raw_path + patient_name + '/' + patient_name + '.clock'
    eeg_trc_file = data_raw_path + patient_name + '/' + patient_name + '_EEG_24h.TRC'
    
    rescaled_video_time = rescale_video_times(video_tps_file, video_clock_file, eeg_trc_file)
    
   


    
    
    
    
if __name__ == "__main__":

    test_rescale_video_times()