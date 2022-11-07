import PySimpleGUI as sg
import soundfile
import glob
import os
from pydub import AudioSegment, effects


### Color settings

scolor="#4f565e"
scolor2="#6c7684"
bgcolor="#4d545e"
windowcolor="#2e3238"

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
	sg.Button("Refresh", button_color=scolor),
	sg.Button("Create Sample Folders", button_color=scolor),
	]]

filelist = [sg.Listbox([], size=(0,16), key= '-LIST-', background_color=bgcolor, text_color="white", expand_x=True, expand_y=True, sbar_background_color=scolor, select_mode=sg.LISTBOX_SELECT_MODE_MULTIPLE, highlight_background_color="DarkGreen", highlight_text_color="white")]

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
	[sg.Checkbox('Suffix', key="-SUFFIXBOOL-", background_color=bgcolor), sg.In(size=(10,0), key="-SUFFIXSTR-")],
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

def make_safedir(path):
	if not os.path.exists(path):
		os.makedirs(path)

def get_filenames(paths):
	fnames = []
	for path in paths:
		fnames.append(os.path.basename(path))
	return fnames

def get_full_foldernames(directory, filenames):
	folnames = []
	for file in filenames:
		folnames.append(directory + "/"+ file)
	return folnames

def update_filelist(showpaths, paths):
	if showpaths:
		window.Element('-LIST-').update(values=paths)
	else:
		window.Element('-LIST-').update(values=get_filenames(paths))

def get_files(directory, recursive):
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

def spawn_popup_samples():
	smpfolderset = False
	samplepack_folderlist = [sg.Column([
	[sg.Text("Drums", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), 
		sg.Checkbox("Drum_Loops", background_color=bgcolor, key="SMP_DRUM_LOOPS"), 
		sg.Text("/", background_color=windowcolor), 
		sg.Checkbox("Cymbal_Loops", background_color="darkslateblue", key="SMP_CYMBAL_LOOPS"), 
		sg.Checkbox("Hat_Loops", background_color="darkslateblue", key="SMP_HAT_LOOPS"), 
		sg.Checkbox("Kick_Loops", background_color="darkslateblue", key="SMP_KICK_LOOPS"), 
		sg.Checkbox("Snare_Loops", background_color="darkslateblue", key="SMP_SNARE_LOOPS"),
		sg.Checkbox("Breakbeat_Loops", background_color="darkslateblue", key="SMP_BREAKBEAT_LOOPS"), 
		sg.Checkbox("Full_Drum_Loops", background_color="darkslateblue", key="SMP_FULL_DRUM_LOOPS"),
		], 
	[sg.Sizer(h_pixels=20), 
		sg.Checkbox("Drum_Hits", background_color=bgcolor, key="SMP_DRUM_HITS"), 
		sg.Text("/", background_color=windowcolor), 
		sg.Checkbox("Cymbals", background_color="darkslateblue", key="SMP_CYMBALS"), 
		sg.Checkbox("Hats", background_color="darkslateblue", key="SMP_HATS"), 
		sg.Checkbox("Kicks", background_color="darkslateblue", key="SMP_KICKS"), 
		sg.Checkbox("Snares", background_color="darkslateblue", key="SMP_SNARES")
		], 
	[sg.Text("Percussion", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Percussion_Loops", background_color=bgcolor, key="SMP_PERCUSSION_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Percussion_Hits", background_color=bgcolor, key="SMP_PERCUSSION_HITS")], 
	[sg.Text("Bass", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Bass Loops", background_color=bgcolor, key="SMP_BASS_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Bass Shots", background_color=bgcolor, key="SMP_BASS_SHOTS")], 
	[sg.Text("Synth", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Synth_Loops", background_color=bgcolor, key="SMP_SYNTH_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Synth_Shots", background_color=bgcolor, key="SMP_SYNTH_SHOTS")], 
	[sg.Text("FX", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Loops", background_color=bgcolor, key="SMP_FX_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Shots", background_color=bgcolor, key="SMP_FX_SHOTS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Downlifters", background_color=bgcolor, key="SMP_FX_DOWNLIFTERS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Uplifters", background_color=bgcolor, key="SMP_FX_UPLIFTERS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Impacts", background_color=bgcolor, key="SMP_FX_IMPACTS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Ambience", background_color=bgcolor, key="SMP_FX_AMBIENCE")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Ambience_Loops", background_color=bgcolor, key="SMP_FX_AMBIENCE_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Glitch", background_color=bgcolor, key="SMP_FX_GLITCH")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Glitch_Loops", background_color=bgcolor, key="SMP_FX_GLITCH_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Textures", background_color=bgcolor, key="SMP_FX_TEXTURES")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("FX_Texture_Loops", background_color=bgcolor, key="SMP_FX_TEXTURE_LOOPS")], 
	[sg.Text("Vocals", background_color=bgcolor)], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Loops", background_color=bgcolor, key="SMP_VOCAL_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Hook_Loops", background_color=bgcolor, key="SMP_VOCAL_HOOK_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Hooks", background_color=bgcolor, key="SMP_VOCAL_HOOKS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Phrase_Loops", background_color=bgcolor, key="SMP_VOCAL_PHRASE_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Phrases", background_color=bgcolor, key="SMP_VOCAL_PHRASES")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Shots", background_color=bgcolor, key="SMP_VOCAL_SHOTS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Chops", background_color=bgcolor, key="SMP_VOCAL_CHOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Chop_Loops", background_color=bgcolor, key="SMP_VOCAL_CHOP_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Ambience", background_color=bgcolor, key="SMP_VOCAL_AMBIENCE")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Ambience_Loops", background_color=bgcolor, key="SMP_VOCAL_AMBIENCE_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Glitch", background_color=bgcolor, key="SMP_VOCAL_GLITCH")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Glitch_Loops", background_color=bgcolor, key="SMP_VOCAL_GLITCH_LOOPS")], 
	[sg.Sizer(h_pixels=20), sg.Checkbox("Vocal_Chants", background_color=bgcolor, key="SMP_VOCAL_CHANTS")], 

	], background_color=windowcolor, scrollable=True, vertical_scroll_only=True, sbar_background_color=bgcolor, expand_x=True, expand_y=True)]
	layout = [samplepack_folderlist,
		[sg.Text('Folder', background_color=bgcolor), 
		sg.In(size=(25,1), enable_events=True ,key='-SMPFOLDER-', readonly=True), 
		sg.FolderBrowse(button_color=scolor)],  
		[sg.Button(button_text="Create", s=10, button_color=bgcolor), sg.Button(button_text="Cancel", s=10, button_color=bgcolor)]
		]
	popup = sg.Window('Sample Pack Generator', layout, background_color=windowcolor, icon=resource_path("data/dtico.ico"), font=("Calibri", 11), resizable=True, size=(1000,1000))
	while True:
		popevent, v = popup.read()
		if popevent in (sg.WIN_CLOSED, 'Exit'):
			break
		if popevent == '-SMPFOLDER-':
			smpfolder = v['-SMPFOLDER-']
			smpfolderset = True
			print(smpfolder)
		if popevent == "Create":
			if smpfolderset:
				#### DRUMS
				os_drumfolder = smpfolder + "/One_Shots/Drums"
				lp_drumfolder = smpfolder + "/Loops/Drum_Loops"
				if v["SMP_DRUM_LOOPS"]:
					make_safedir(lp_drumfolder)
					if v["SMP_CYMBAL_LOOPS"]:
						make_safedir(lp_drumfolder + "/Cymbal_Loops")
					if v["SMP_HAT_LOOPS"]:
						make_safedir(lp_drumfolder + "/Hat_Loops")
					if v["SMP_KICK_LOOPS"]:
						make_safedir(lp_drumfolder + "/Kick_Loops")
					if v["SMP_SNARE_LOOPS"]:
						make_safedir(lp_drumfolder + "/Snare_Loops")
					if v["SMP_BREAKBEAT_LOOPS"]:
						make_safedir(lp_drumfolder + "/Breakbeat_Loops")
					if v["SMP_FULL_DRUM_LOOPS"]:
						make_safedir(lp_drumfolder + "/Full_Drum_Loops")
				if v["SMP_DRUM_HITS"]:
					make_safedir(os_drumfolder)
					if v["SMP_CYMBALS"]:
						make_safedir(os_drumfolder + "/Cymbals")
					if v["SMP_HATS"]:
						make_safedir(os_drumfolder + "/Hats")
					if v["SMP_KICKS"]:
						make_safedir(os_drumfolder + "/Kicks")
					if v["SMP_SNARES"]:
						make_safedir(os_drumfolder + "/Snares")

				##### PERC
				if v["SMP_PERCUSSION_LOOPS"]:
					make_safedir(smpfolder + "/Loops/Percussion_Loops")
				if v["SMP_PERCUSSION_HITS"]:
					make_safedir(smpfolder + "/One_Shots/Percussion")

				#### BASS
				if v["SMP_BASS_LOOPS"]:
						make_safedir(smpfolder + "/Loops/Bass_Loops")
				if v["SMP_BASS_SHOTS"]:
						make_safedir(smpfolder + "/One_Shots/Bass_Shots")

				#### SYNTHS
				if v["SMP_SYNTH_LOOPS"]:
					make_safedir(smpfolder + "/Loops/Synth_Loops")
				if v["SMP_SYNTH_SHOTS"]:
					make_safedir(smpfolder + "/One_Shots/Synth_Shots")


				### FX
				os_fxfolder = smpfolder + "/One_Shots/FX"
				lp_fxfolder = smpfolder + "/Loops/FX_Loops"
				if v["SMP_FX_LOOPS"]:
					make_safedir(lp_fxfolder + "/SFX_Loops")
				if v["SMP_FX_SHOTS"]:
					make_safedir(os_fxfolder + "/SFX_Shots")
				if v["SMP_FX_DOWNLIFTERS"]:
					make_safedir(os_fxfolder + "/FX_Downlifters")
				if v["SMP_FX_UPLIFTERS"]:
					make_safedir(os_fxfolder + "/FX_Uplifters")
				if v["SMP_FX_IMPACTS"]:
					make_safedir(os_fxfolder + "/FX_Impacts")
				if v["SMP_FX_AMBIENCE"]:
					make_safedir(os_fxfolder + "/FX_Ambience")
				if v["SMP_FX_AMBIENCE_LOOPS"]:
					make_safedir(lp_fxfolder + "/FX_Ambience_Loops")
				if v["SMP_FX_GLITCH"]:
					make_safedir(os_fxfolder + "/FX_Glitch")
				if v["SMP_FX_GLITCH_LOOPS"]:
					make_safedir(lp_fxfolder + "/FX_Glitch_Loops")
				if v["SMP_FX_TEXTURES"]:
					make_safedir(lp_fxfolder + "/FX_Textures")
				if v["SMP_FX_TEXTURE_LOOPS"]:
					make_safedir(lp_fxfolder + "/FX_Texture_Loops")

				### VOCAL
				os_vocfolder = smpfolder + "/One_Shots/Vocals"
				lp_vocfolder = smpfolder + "/Loops/Vocal_Loops"
				if v["SMP_VOCAL_LOOPS"]:
					make_safedir(lp_vocfolder)
				if v["SMP_VOCAL_SHOTS"]:
					make_safedir(os_vocfolder + "/Vocal_Shots")
				if v["SMP_VOCAL_CHOPS"]:
					make_safedir(os_vocfolder + "/Vocal_Chops")
				if v["SMP_VOCAL_PHRASE_LOOPS"]:
					make_safedir(lp_vocfolder + "/Vocal_Phrase_Loops")
				if v["SMP_VOCAL_HOOK_LOOPS"]:
					make_safedir(lp_vocfolder + "/Vocal_Hook_Loops")
				if v["SMP_VOCAL_PHRASES"]:
					make_safedir(os_vocfolder + "/Vocal_Phrases")
				if v["SMP_VOCAL_HOOKS"]:
					make_safedir(os_vocfolder + "/Vocal_Hooks")
				if v["SMP_VOCAL_CHOP_LOOPS"]:
					make_safedir(lp_vocfolder + "/Vocal_Chop_Loops")
				if v["SMP_VOCAL_AMBIENCE"]:
					make_safedir(os_vocfolder + "/Vocal_Ambience")
				if v["SMP_VOCAL_CHANTS"]:
					make_safedir(os_vocfolder + "/Vocal_Chants")
				if v["SMP_VOCAL_AMBIENCE_LOOPS"]:
					make_safedir(lp_vocfolder + "/Vocal_Ambience_Loops")
				if v["SMP_VOCAL_GLITCH"]:
					make_safedir(os_vocfolder + "/Vocal_Glitch")
				if v["SMP_VOCAL_GLITCH_LOOPS"]:
					make_safedir(lp_vocfolder + "/Vocal_Glitch_Loops")



				#####
				popup.close()
				filelog(f"Successfully created sample pack structure in {smpfolder}!")
		if popevent == "Cancel":
			popup.close()

### Modules

def trim_silence(files):
	for file in files:
		fname = os.path.basename(file)
		sound = AudioSegment.from_file(file)
		start_trim = detect_leading_silence(sound)
		end_trim = detect_leading_silence(sound.reverse())
		duration = len(sound)
		trimmed_sound = sound[start_trim:duration - end_trim]
		trimmed_sound.export(file, format="wav")
		filelog("Trimmed " + fname)

def convert_bitrate(files):
	bitrate = str(values['-BITRATE-'])
	for file in files:
		fname = os.path.basename(file)
		data, samplerate = soundfile.read(file)
		soundfile.write(file, data, samplerate, subtype='PCM_' + bitrate)
		filelog("Converting " + fname + " to " + bitrate + " - bit")

def convert_samplerate(files):
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

def set_prefix(files, prefix):
	curproc = 0
	newfiles = []
	for file in files:
		fname = os.path.basename(file)
		d = os.path.dirname(file)
		os.rename(file, d + "/" + prefix + fname)
		filelog("Renamed to " + prefix + fname)
		curproc += 1
		newfiles.append(d + "/" + prefix + fname)
	return newfiles

def set_suffix(files, suffix):
	curproc = 0
	newfiles = []
	for file in files:
		fname = os.path.basename(file).split(".")[0]
		d = os.path.dirname(file)
		os.rename(file, d + "/" + fname + suffix + ".wav")
		filelog("Renamed to " + fname + suffix + ".wav")
		curproc += 1
		newfiles.append(d + "/" + fname + suffix + ".wav")
	return newfiles

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
			update_filelist(values["-SHOWPATHS-"], get_files(d, values['-REC-']))


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
		currentfiles = get_files(folder, values['-REC-'])
		update_filelist(values["-SHOWPATHS-"], currentfiles)
		folderset = True
	if event == 'Refresh':
		if folderset == True:
			currentfiles = get_files(folder, values['-REC-'])
			update_filelist(values["-SHOWPATHS-"], currentfiles)	

	if event == '-REC-':
		if folderset == True:
			currentfiles = get_files(folder, values['-REC-'])
			update_filelist(values["-SHOWPATHS-"], currentfiles)

	if event == '-SHOWPATHS-':
		if folderset == True:
			currentfiles = get_files(folder, values['-REC-'])
			update_filelist(values["-SHOWPATHS-"], currentfiles)
	if event == 'Create Sample Folders':
		spawn_popup_samples()


	if event == 'Process':
		if folderset == True:
			if values['-LIST-'] != []:
				currentfiles = get_full_foldernames(folder, values['-LIST-'])
			else:
				currentfiles = get_files(folder, values['-REC-'])
			try:
				if values['-TRIM-'] == True:
					trim_silence(currentfiles)
				if values['-NORM-'] == True:
					normalize(currentfiles)            
				if values['-BIT-'] == True:
					convert_bitrate(currentfiles)
				if values['-SMPRATE-'] == True:
					convert_samplerate(currentfiles)
				if values['-PREFIXBOOL-'] == True:
					currentfiles = set_prefix(currentfiles, values["-PREFIXSTR-"])
				if values['-SUFFIXBOOL-'] == True:
					currentfiles = set_suffix(currentfiles, values["-SUFFIXSTR-"])
				if values['-REPL-'] == True:
					findrepl(currentfiles, values["-RPLFROM-"], values["-RPLTO-"])


##### Destructive, should be last!
				if values['-EMPTY-'] == True:
					rmempty(currentfiles, values['-EMPTYFL-'])
				update_filelist(values["-SHOWPATHS-"], get_files(folder, values['-REC-']))


			except NameError as error:
				filelog(error)

window.close()