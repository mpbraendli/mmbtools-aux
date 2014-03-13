#!/bin/bash
#
# Read audio from ALSA input using gstreamer, and encode with fdk-aac-dabplus-zmq
#
BITRATE=$1
DSTPORT=$2
QUEUEDELAY=400000 #400ms

GSTREAMER_VERSION="0"

if [ "$DSTPORT" == "" ]
then
    echo "Usage:"
    echo " $0 <bitrate> <zmq destination>"
    exit 1
fi


if [ "$GSTREAMER_VERSION" == "1" ]
then
    gst-launch-1.0 -q \
        alsasrc "device=default" ! \
        audio/x-raw, 'rate=48000,format=S16LE,channels=2' ! \
        queue "max-size-time=$QUEUEDELAY" ! \
        filesink location="/dev/stdout" | \
        dabplus-enc-file-zmq \
            -i /dev/stdin -b $BITRATE -f raw -a -o "${DSTPORT}"

elif [ "$GSTREAMER_VERSION" == "0" ]
then
    gst-launch -q \
        alsasrc "device=default" ! \
        audio/x-raw-int, 'rate=48000,format=S16LE,channels=2' ! \
        queue "max-size-time=$QUEUEDELAY" ! \
        filesink location="/dev/stdout" | \
        dabplus-enc-file-zmq \
            -i /dev/stdin -b $BITRATE -f raw -a -o "${DSTPORT}"
fi

