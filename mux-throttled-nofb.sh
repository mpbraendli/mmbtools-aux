#!/bin/bash

# run this with -s

../crc-dabmux-0.3.0.4/src/CRC-DabMux -o -L "TuxMux" $* -r \
    -A funk.mp2 -b 128 -i 10 -S -L "Funk" -C \
    -A luschtig.mp2 -b 128 -i 3 -S -L "Luschtig" -C \
    -O fifo:///dev/stdout?type=raw
    #-O fifo:///dev/stdout

    #-A 1.ff -b 128 -i 4 -S -L "Banane" -C \
#   -O udp://0.0.0.0:54000?type=raw

#CRC-DabMux -L "TuxMux"  \
#    -A 1.ff -b 128 -i 10 -S -L "L2_128" -C \
#    -F 2.ff -k -b 48 -i 2 -S -L "AAC48" -C \
#    -F 3.ff -k -b 64 -i 3 -S -L "AAC64" -C \
#    -F 4.ff -k -b 128 -i 4 -S -L "AAC128" -C \
#    -O fifo:///dev/stdout
