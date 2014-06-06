#!/bin/bash
# encode audio from my snd-aloop sound card

dabplus-enc -d hw:1 -c 2 -r 32000 -b 64 -o tcp://localhost:9000 -l
