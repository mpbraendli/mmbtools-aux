#!/bin/bash
#
# Encode Frequence Banane to ZMQ
#
# Remarks: it's probably better to use the
# snd-aloop scenario now.

WITH_GSTREAMER=0
URL=http://fbpc5.epfl.ch:8000/fb_192
BITRATE=$1
DST=$2

if [ "$DST" == "" ]
then
    echo "Usage:"
    echo " $0 <bitrate> <zmq destination>"
    exit 1
fi

if [ "$WITH_GSTREAMER" == "1" ]
then
    gst-launch-0.10 -q \
        uridecodebin uri=$URL ! \
        queue ! \
        audioresample quality=8 ! \
        audioconvert ! \
        audio/x-raw-int, 'rate=48000,format=S16LE,channels=2' ! \
        filesink location="/dev/stdout" | \
        dabplus-enc \
            -i /dev/stdin -b $BITRATE -f raw -a -o $DST
else
    mpg123 -s $URL |\
        sox -t raw -r 44100 -e signed -b 16 -c 2 -   -t raw  - rate 32k |\
        dabplus-enc \
            -i /dev/stdin -r 32000 -b $BITRATE -f raw -a -o $DST
fi
