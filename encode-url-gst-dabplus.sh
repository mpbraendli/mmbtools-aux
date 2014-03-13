#!/bin/bash
#
# Read a URL using gstreamer, and encode with fdk-aac-dabplus-zmq
#
URL=$1
BITRATE=$2
DSTPORT=$3
QUEUEDELAY=400000 #400ms

GSTREAMER_VERSION="1"

if [ "$DSTPORT" == "" ]
then
    echo "Usage:"
    echo " $0 <url> <bitrate> <zmq destination>"
    exit 1
fi


if [ "$GSTREAMER_VERSION" == "1" ]
then
    gst-launch-1.0 -q \
        uridecodebin uri=$URL ! \
        queue "max-size-time=$QUEUEDELAY" ! \
        audioresample quality=8 ! \
        audioconvert ! \
        audio/x-raw, 'rate=48000,format=S16LE,channels=2' ! \
        filesink location="/dev/stdout" | \
        dabplus-enc-file-zmq \
            -i /dev/stdin -b $BITRATE -f raw -a -o "${DSTPORT}"

elif [ "$GSTREAMER_VERSION" == "0" ]
then
    gst-launch -q \
        uridecodebin uri=$URL ! \
        queue "max-size-time=$QUEUEDELAY" ! \
        audioresample quality=8 ! \
        audioconvert ! \
        audio/x-raw-int, 'rate=48000,format=S16LE,channels=2' ! \
        filesink location="/dev/stdout" | \
        dabplus-enc-file-zmq \
            -i /dev/stdin -b $BITRATE -f raw -a -o "${DSTPORT}"
fi

