import PySimpleGUI as sg
import soundfile
import glob
import os
from pydub import AudioSegment, effects


### Color settings

scolor="violetred3"
scolor2="DeepPink4"
bgcolor="snow4"
windowcolor="grey18"

## PyInstaller Path Converter

def resource_path(relative_path):
    """ Get absolute path to resource, works for dev and for PyInstaller """
    try:
        # PyInstaller creates a temp folder and stores path in _MEIPASS
        base_path = sys._MEIPASS
    except Exception:
        base_path = os.path.abspath(".")

    return os.path.join(base_path, relative_path)

#### Layout


selector = [[
	sg.Text('Folder', background_color=bgcolor), 
	sg.In(size=(25,1), enable_events=True ,key='-FOLDER-', readonly=True), 
	sg.FolderBrowse(button_color=scolor), 
	sg.Checkbox('Iterate down folder tree? (Recursive)', key="-REC-", enable_events=True, background_color=scolor),
	sg.Checkbox('Show paths?', key="-SHOWPATHS-", enable_events=True, background_color=scolor),
	sg.Button("Refresh", button_color=scolor)
	]]

filelist = [sg.Listbox([], size=(0,16), key= '-LIST-', background_color=bgcolor, text_color="white", expand_x=True, expand_y=True, sbar_background_color=scolor)]

loglist = [sg.Listbox([], no_scrollbar=True, size=(0,8), key= '-LOG-', background_color=scolor2, text_color="white", expand_x=True)]
log = []

modulecol1 = sg.Column([
	[sg.Checkbox('Trim leading/ending silence', key='-TRIM-', background_color=bgcolor)], 
	[sg.Checkbox('Normalize peak with', key='-NORM-', background_color=bgcolor), sg.In("1", size=(3,3), key='-HEADRM-', ), sg.Text('db headroom', background_color=bgcolor)],
	[sg.Checkbox('Convert bitrate', key="-BIT-", background_color=bgcolor), sg.Combo([16, 24], default_value=24, button_background_color=scolor, key='-BITRATE-', readonly=True), sg.Text("BIT",background_color=bgcolor)],
	[sg.Checkbox('Convert samplerate', key="-SMPRATE-", background_color=bgcolor), sg.Combo([44100, 48000, 96000, 192000], default_value=44100, button_background_color=scolor, key='-SAMPLERATE-', readonly=True), sg.Text("Hz",background_color=bgcolor)],	
	[sg.Checkbox('Delete empty audio files', key="-EMPTY-", background_color=bgcolor)],
	[sg.Checkbox('Include _Master / _Current files? (FL)',default=True, key="-EMPTYFL-", pad=(30,0), background_color=bgcolor,)]
	],
	vertical_alignment="top",
	background_color=bgcolor,
	expand_y=True)

modulecol2 = sg.Column([
	[sg.Checkbox('Prefix', key="-PREFIXBOOL-", background_color=bgcolor), sg.In(size=(10,0), key="-PREFIXSTR-")],
	[sg.Checkbox('Replace Text', key="-REPL-", background_color=bgcolor), sg.In(size=(10,0), key="-RPLFROM-", enable_events=True), sg.Text('>>>', background_color=bgcolor), sg.In(size=(10,0), key="-RPLTO-")]
	], 
	vertical_alignment="top",
	background_color=bgcolor,
	expand_y=True)


modulelist = [modulecol1, modulecol2]

bottomcol = sg.Column([[sg.Button("Process", button_color=scolor, size=30, border_width=4)], loglist], element_justification="c", justification="c", expand_x=True, background_color=windowcolor)
folderset = False

layout = [[
	filelist,
	selector,
	[sg.HorizontalSeparator(pad=(0,10))],
	modulelist,
	[sg.HorizontalSeparator(pad=(0,10))],
	bottomcol
	]]


window = sg.Window('ABS', layout,resizable=True, finalize=True, background_color=windowcolor, size=(960,800), icon=resource_path("data/dtico.ico"), font=("Calibri", 11))

### Helpers

def getfilenames(paths):
	fnames = []
	for path in paths:
		fnames.append(os.path.basename(path))
	return fnames

def updatefilelist(showpaths, paths):
	if showpaths:
		window.Element('-LIST-').update(values=paths)
	else:
		window.Element('-LIST-').update(values=getfilenames(paths))

def getfiles(directory, recursive):
	filelog(f"Checking for wavs in {directory}")
	files = []
	for file in glob.glob(f"{directory}/*.wav", recursive=recursive):
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
		fname = os.path.basename(file)
		sound = AudioSegment.from_file(file)
		start_trim = detect_leading_silence(sound)
		end_trim = detect_leading_silence(sound.reverse())
		duration = len(sound)
		trimmed_sound = sound[start_trim:duration - end_trim]
		trimmed_sound.export(file, format="wav")
		filelog("Trimmed " + fname)

def convertbitrate(files):
	bitrate = str(values['-BITRATE-'])
	for file in files:
		fname = os.path.basename(file)
		data, samplerate = soundfile.read(file)
		soundfile.write(file, data, samplerate, subtype='PCM_' + bitrate)
		filelog("Converting " + fname + " to " + bitrate + " - bit")

def convertsamplerate(files):
	samplerate = int(values['-SAMPLERATE-'])
	for file in files:
		fname = os.path.basename(file)
		ob = soundfile.SoundFile(file)
		data, samplerate = soundfile.read(file)
		soundfile.write(file, data, samplerate, subtype=ob.subtype)
		filelog("Converting " + fname + " to " + str(samplerate) + " - bit")

def normalize(files):
	headroom = values['-HEADRM-']
	if headroom == '':
		filelog('Please fill in the headroom amount to normalize!')
	else:
		try:
			hrval = int(headroom)
			for file in files:
				fname = os.path.basename(file)
				sound = AudioSegment.from_file(file, "wav")
				normalized_sound = effects.normalize(sound, headroom=hrval)
				normalized_sound.export(file, format="wav")
				filelog("Normalizing " + fname)
		except:
			filelog('Please fill the headroom amount with a number to normalize!')


def rmempty(files, FLStudio):
	for file in files:
		fname = os.path.basename(file)
		audio = AudioSegment.from_file(file)
		loudness = audio.dBFS
		if FLStudio:
			if loudness == float('-inf') or file.endswith(("_Master.wav", "_Current.wav")) or "SC" in file:
				filelog("Removing " + fname)
				os.remove(file)
		else:
			if loudness == float('-inf'):
				filelog("Removing " + fname)
				os.remove(file)

def setprefix(files, prefix):
	curproc = 0
	for file in files:
		fname = os.path.basename(file)
		d = os.path.dirname(file)
		os.rename(file, d + "/" + prefix + fname)
		filelog("Renamed to " + prefix + fname)
		curproc += 1
		if curproc == len(files):
			updatefilelist(values["-SHOWPATHS-"], getfiles(d, values['-REC-']))

def findrepl(files, rplfrom, rplto):
	curproc = 0
	for file in files:
		fname = os.path.basename(file)
		newfname = fname.replace(rplfrom, rplto)
		d = os.path.dirname(file)
		filelog("Renamed " + fname + " to " + newfname)
		os.rename(file, d + "/" + newfname)
		curproc += 1
		if curproc == len(files):
			updatefilelist(values["-SHOWPATHS-"], getfiles(d, values['-REC-']))


### GUI Logic

def filelog(logmsg):
	log.append(logmsg)
	window.Element('-LOG-').update(log, scroll_to_index=len(log))

filelog("Ready to juice! By Dion Timmer")

## Event Loop

while True:
	event, values = window.read()
	if event in (sg.WIN_CLOSED, 'Exit'):
		break
	if event == '-FOLDER-':
		folder = values['-FOLDER-']
		currentfiles = getfiles(folder, values['-REC-'])
		updatefilelist(values["-SHOWPATHS-"], currentfiles)
		folderset = True
		filelog("Folder Set")
	if event == 'Refresh':
		if folderset == True:
			currentfiles = getfiles(folder, values['-REC-'])
			updatefilelist(values["-SHOWPATHS-"], currentfiles)	

	if event == '-REC-':
		if folderset == True:
			currentfiles = getfiles(folder, values['-REC-'])
			updatefilelist(values["-SHOWPATHS-"], currentfiles)

	if event == '-SHOWPATHS-':
		if folderset == True:
			currentfiles = getfiles(folder, values['-REC-'])
			updatefilelist(values["-SHOWPATHS-"], currentfiles)


	if event == 'Process':
		if folderset == True:
			currentfiles = getfiles(folder, values['-REC-'])
			try:
				if values['-TRIM-'] == True:
					trimsilence(currentfiles)
				if values['-NORM-'] == True:
					normalize(currentfiles)            
				if values['-BIT-'] == True:
					convertbitrate(currentfiles)
				if values['-SMPRATE-'] == True:
					convertsamplerate(currentfiles)
				if values['-PREFIXBOOL-'] == True:
					setprefix(currentfiles, values["-PREFIXSTR-"])
				if values['-REPL-'] == True:
					try:
						findrepl(currentfiles, values["-RPLFROM-"], values["-RPLTO-"])
					except FileNotFoundError:
						findrepl(getfiles(folder, values['-REC-']), values["-RPLFROM-"], values["-RPLTO-"])


##### Destructive, should be last!
				if values['-EMPTY-'] == True:
					rmempty(currentfiles, values['-EMPTYFL-'])


			except NameError as error:
				filelog(error)

window.close()