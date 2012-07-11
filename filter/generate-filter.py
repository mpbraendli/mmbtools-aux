#!/usr/bin/env python
import gnuradio
from gnuradio import gr

gain = 1
rate = 2.048e6
cutoff = 810e3
transition_width = 150e3
taps = gr.firdes_low_pass(gain, rate, cutoff, transition_width, gr.firdes.WIN_HAMMING, beta=6.76)

print(len(taps))
for t in taps:
    print(t)
