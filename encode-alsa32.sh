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

dabplus-enc -d $ALSASRC -c 2 -r 32000 -b $BITRATE -o $DST -p 48

