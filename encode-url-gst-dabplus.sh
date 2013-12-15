#!/bin/bash
#
# Read a URL using gstreamer, and encode with fdk-aac-dabplus-zmq
#
URL=$1
BITRATE=$2
DSTPORT=$3
QUEUEDELAY=400000 #400ms

if [ "$DSTPORT" == "" ]
then
    echo "Usage:"
    echo " $0 <url> <bitrate> <zmq destination port>"
    exit 1
fi


gst-launch-1.0 -q \
    uridecodebin uri=$URL ! \
    queue "max-size-time=$QUEUEDELAY" ! \
    audioresample quality=8 ! \
    audioconvert ! \
    audio/x-raw, 'rate=48000,format=S16LE,channels=2' ! \
    filesink location="/dev/stdout" | \
    ../fdk-aac-dabplus/aac-enc-dabplus-zmq \
        -i /dev/stdin -b $BITRATE -f raw -a -o "tcp://*:${DSTPORT}"
