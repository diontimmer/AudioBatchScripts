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

#### Layout


selector = [[
	sg.Text('Folder', background_color=bgcolor), 
	sg.In(size=(25,1), enable_events=True ,key='-FOLDER-',background_color="snow1", readonly=True), 
	sg.FolderBrowse(button_color=scolor), 
	sg.Checkbox('Iterate down folder tree? (Recursive)', key="-REC-", enable_events=True, background_color=scolor),
	sg.Checkbox('Show paths?', key="-SHOWPATHS-", enable_events=True, background_color=scolor),
	sg.Button("Refresh", button_color=scolor)
	]]

filelist = [sg.Listbox([], size=(0,16), key= '-LIST-', background_color=bgcolor, text_color="white", expand_x=True, sbar_background_color=scolor)]

loglist = [sg.Listbox([], no_scrollbar=True, size=(0,8), key= '-LOG-', background_color=scolor2, text_color="white", expand_x=True)]
log = []

modulecol1 = sg.Column([
	[sg.Checkbox('Trim Leading Silence', key='-TRIM-', background_color=bgcolor)], 
	[sg.Checkbox('Normalize peak to 0db', key='-NORM-', background_color=bgcolor)],
	[sg.Checkbox('Convert 32Bit to 24Bit', key="-BIT-", background_color=bgcolor)],
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

window = sg.Window('ABS', layout,resizable=True, finalize=True, background_color=windowcolor, size=(960,712))


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
		fname = os.path.basename(file)
		sound = AudioSegment.from_file(file)
		start_trim = detect_leading_silence(sound)
		end_trim = detect_leading_silence(sound.reverse())
		duration = len(sound)
		trimmed_sound = sound[start_trim:duration - end_trim]
		trimmed_sound.export(file, format="wav")
		filelog("Trimmed " + fname)

def process_32to24(files):
	for file in files:
		fname = os.path.basename(file)
		if(file.endswith('.wav')):
			data, samplerate = soundfile.read(file)
			soundfile.write(file, data, samplerate, subtype='PCM_24')
			filelog("Converting " + fname + " to 24 - bit")

def normalize(files):
	for file in files:
		fname = os.path.basename(file)
		sound = AudioSegment.from_file(file, "wav")
		normalized_sound = effects.normalize(sound, headroom=0)
		normalized_sound.export(file, format="wav")
		filelog("Normalizing " + fname)

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
	window.Element('-LOG-').update(log)

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
					process_32to24(currentfiles)
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