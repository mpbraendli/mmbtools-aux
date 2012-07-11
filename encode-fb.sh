#!/bin/bash
echo "Encoding FB to 1.ff"
mpg123 -r 48000 -s http://fbpc5.epfl.ch:8001 |toolame -s 48 -D 4 -b 128 /dev/stdin ./1.ff
