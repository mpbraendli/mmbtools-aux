#!/bin/bash
#
# Encode Frequence Banane to ZMQ tcp://*:2720
#
mpg123 -s http://fbpc5.epfl.ch:8000/fb_192 |\
    sox -t raw -r 44100 -e signed -b 16 -c 2 -   -t raw  - rate 48k |\
    ../fdk-aac-dabplus/aac-enc-dabplus-zmq -i /dev/stdin -b 96 -f raw -a -o 'tcp://*:2720'
