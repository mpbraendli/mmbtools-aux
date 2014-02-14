#!/bin/bash
#
# Encode Frequence Banane to ZMQ tcp://*:2720
#

WITH_GSTREAMER=0
URL=http://fbpc5.epfl.ch:8000/fb_192
BITRATE=$1
DSTPORT=$2

if [ "$DSTPORT" == "" ]
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
        ../fdk-aac-dabplus/aac-enc-dabplus-zmq -i /dev/stdin \
            -b $BITRATE -f raw -a -o $DSTPORT
else
    mpg123 -s $URL |\
        sox -t raw -r 44100 -e signed -b 16 -c 2 -   -t raw  - rate 48k |\
        ../fdk-aac-dabplus/aac-enc-dabplus-zmq -i /dev/stdin \
            -b $BITRATE -f raw -a -o $DSTPORT
fi
