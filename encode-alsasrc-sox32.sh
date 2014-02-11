#!/bin/bash
#
# Read audio from ALSA input using sox, and encode with fdk-aac-dabplus-zmq
#
BITRATE=$1
DST=$2
ALSASRC="default"

if [ "$DST" == "" ]
then
    echo "Usage:"
    echo " $0 <bitrate> <zmq destination>"
    exit 1
fi

sox -t alsa $ALSASRC -b 16 -t raw - rate 32k channels 2 | \
    ../fdk-aac-dabplus/aac-enc-dabplus-zmq -r 32000 \
    -i /dev/stdin -b $BITRATE -f raw -a -o $DST

