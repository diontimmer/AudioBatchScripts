import PySimpleGUI as sg
import soundfile
import glob
import os
from pydub import AudioSegment, effects




#### Layout


selector = [[sg.Text('Folder'), sg.In(size=(25,1), enable_events=True ,key='-FOLDER-'), sg.FolderBrowse()]]

filelist = [sg.Listbox([], size=(128,16), key= '-LIST-', background_color="purple", text_color="white")]

loglist = [sg.Listbox([], no_scrollbar=True, size=(128,8), key= '-LOG-', background_color="dark slate blue", text_color="white")]
log = []

modulecol = [
	[sg.Checkbox('Trim Leading Silence', key='-TRIM-')], 
	[sg.Checkbox('Normalize peak to 0db', key='-NORM-')],
	[sg.Checkbox('Convert 32Bit to 24Bit', key="-BIT-")],
	[sg.Checkbox('Delete empty audio files', key="-EMPTY-")],
	[sg.Checkbox('Include _Master / _Current files? (FL)',default=True, key="-EMPTYFL-", pad=(30,0), background_color="purple")],




	]

bottomcol = [sg.Button("Process"), sg.Checkbox('Iterate down folder tree? (Recursive)', key="-REC-", enable_events=True)]
folderset = False

layout = [[
	filelist,
	selector, 
	modulecol,
	bottomcol,
	loglist,
	]]


sg.theme("DarkPurple1")
window = sg.Window('Dions Scripts V1', layout,resizable=False, finalize=True)


### helpers

def getfiles(directory, recursive):
    files = []
    for file in glob.iglob(directory + '**/**', recursive=recursive):
        if(file.endswith('.wav')):
            files.append(file)
    if len(files) == 0:
        filelog("No valid wavs found!")
    return files

def detect_leading_silence(sound, silence_threshold=-50.0, chunk_size=1):
    trim_ms = 0
    assert chunk_size > 0
    while sound[trim_ms:trim_ms+chunk_size].dBFS < silence_threshold and trim_ms < len(sound):
        trim_ms += chunk_size

    return trim_ms

### Modules

def trimsilence(files):
    for file in files:
        sound = AudioSegment.from_file(file)
        start_trim = detect_leading_silence(sound)
        end_trim = detect_leading_silence(sound.reverse())
        duration = len(sound)
        trimmed_sound = sound[start_trim:duration - end_trim]
        trimmed_sound.export(file, format="wav")
        filelog("Trimmed " + file)


def process_32to24(files):
    for file in files:
        if(file.endswith('.wav')):
            data, samplerate = soundfile.read(file)
            soundfile.write(file, data, samplerate, subtype='PCM_24')
            filelog("Converting " + file + " to 24 - bit")


def normalize(files):
    for file in files:
        sound = AudioSegment.from_file(file, "wav")
        normalized_sound = effects.normalize(sound, headroom=0)
        normalized_sound.export(file, format="wav")
        filelog("Normalizing " + file)


def rmempty(files):
    for file in files:
        audio = AudioSegment.from_file(file)
        loudness = audio.dBFS
        if loudness == float('-inf') or file.endswith(("_Master.wav", "_Current.wav")) or "SC" in file:
            filelog("Removing " + str(file))
            os.remove(file)


### GUI Logic

def filelog(logmsg):
	log.append(logmsg)
	window.Element('-LOG-').update(log)

filelog("Ready to juice! By Dion Timmer")

     
while True:
    event, values = window.read()
    if event in (sg.WIN_CLOSED, 'Exit'):
        break
    if event == '-FOLDER-':
        folder = values['-FOLDER-']
        currentfiles = getfiles(folder, values['-REC-'])
        window.Element('-LIST-').update(values=currentfiles)
        folderset = True
        filelog("Folder Set")

    if event == '-REC-':
        if folderset == True:
        	currentfiles = getfiles(folder, values['-REC-'])
        	window.Element('-LIST-').update(values=currentfiles)

    if event == 'Process':
    	if folderset == True:
	    	currentfiles = getfiles(folder, values['-REC-'])
	    	try:    		
	    		if values['-BIT-'] == True:
	    			process_32to24(currentfiles)
	    		if values['-TRIM-'] == True:
	    			trimsilence(currentfiles)
	    		if values['-NORM-'] == True:
	    			normalize(currentfiles)
	    		if values['-EMPTY-'] == True:
	    			rmempty(currentfiles)



	    	except NameError as error:
	    		filelog(error)

window.close()