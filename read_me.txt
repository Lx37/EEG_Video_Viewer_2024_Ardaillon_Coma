#####################################################################
###                          Coma Viewer                          ###
###                  Hugo Ardaillon's project 2024                ###
###                  Data from Florent Gobert (2014)              ###
###           code developped by : A.Corneyllie - H.Ardaillon     ###
#####################################################################


** Raw Data Infos ** :
.TRC 	→ EEG
.avi	→ video
.tps    → video frame timming (to be resync with EEG) - encoding: U32, data in ms
.clock	→ video trigger times sent by Micromed for temporal linear regression - encoding: U32, data in ms
.raw	→ sonometre, luxmetre and syncrho times for temporal linear regression - data in float64
.header	→ data header for raw (sonometre, luxmetre)
.fac    → eye/motor activity score, synchronized with video .clock
.facdef 

 Video  Sample rate : 1 Hz
 Raw    Sample rate : 10 Hz

 Data_path : crnldata/cap/Data/data_coma/data_coma_sommeil/patients


 This viewver show synchronized EEG, video, and raw data (sonometre and luxmetre).
 (+ soon: eye/motor scores)
 It allows for the entry of labeled epochs encoding [...].

Runing on python 
See requirements.txt for list of python packages

