#!/bin/sh

../crc-dabmod-0.3.3/src/crc-dabmod /dev/stdin -g2 $* -l -u "master_clock_rate=32768000,type=b100" -F 234208000
