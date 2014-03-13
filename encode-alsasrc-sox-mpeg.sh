#!/bin/bash
#
# Read audio from ALSA input using sox, and encode with toolame,
# send to ZMQ
#
# This needs toolame-dab from
# https://github.com/Opendigitalradio/toolame-dab
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

sox -t alsa $ALSASRC -b 16 -t raw - rate 48k channels 2 | \
    toolame -s 48 -D 4 -b $BITRATE /dev/stdin $DST

