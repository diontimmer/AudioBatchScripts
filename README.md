# AudioBatchScripts
This is ABS, a list of highly powerful batch file processing functions wrapped in a GUI.
They are used to quickly edit a ton of audio files at once (ie stems, sample packs).
These tools require python 3 to run properly.

It can currently process single folders, or an entire structure recursively.
These tools include:
- Normalize peaks to 0db
- Trim leading and ending silence
- Remove empty wav files (Aswell as _Current & _Master files for FL)
- Convert 32bit to 24bit for compatibility of certain programs
- Add prefixes to your files (KICK_Filename.wav)
- Find and replace text.
- resampling is broken

To install:
Download a built .exe from [here](https://www.github.com/diontimmer/AudioBatchScripts/releases/latest/download/ABS.exe) and run it.

If the .exe doesnt run on your computer, you can try building it yourself:
Download the source code above. Run the install.bat script, once thats finished run the buildexe script. The .exe should be in the binaries folder.
If this does not work you can also run the python script directly after installing the requirements.

If all above fails you are out of luck and should probably contact me :)

![alt text](https://www.dropbox.com/s/8bjl9axq6dzjw0x/absimg.PNG?raw=1 "ABS")
