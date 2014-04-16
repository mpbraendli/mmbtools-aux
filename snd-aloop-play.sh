#!/bin/bash
#
# Play a file to my snd-aloop soundcard
mplayer -ao alsa:device=hw=1.1 -srate 32000 **/*mp3
