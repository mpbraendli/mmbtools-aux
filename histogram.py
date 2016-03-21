#!/usr/bin/python2
#
# Print sample histograms from dabmod I/Q file

import sys

import pylab as P
import numpy


fd = open('test.iq', 'rb')

read_data = numpy.fromfile(file=fd, dtype=numpy.float32, count=-1)

print("MAX absolute value: {}".format(numpy.max(numpy.abs(read_data))))

if 0:
    P.plot(read_data)

if 1:
    P.figure()

    # the histogram of the data with histtype='step'
    n, bins, patches = P.hist(read_data, 50, normed=1, histtype='stepfilled')
    P.setp(patches, 'facecolor', 'g', 'alpha', 0.75)

P.show()

