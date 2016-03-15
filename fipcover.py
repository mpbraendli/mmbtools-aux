#!/usr/bin/env python2
# -*- coding: utf-8 -*-
#
# Download the cover from the fip website
#
# The MIT License (MIT)
#
# Copyright (c) 2016 Matthias P. Braendli
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
#    The above copyright notice and this permission notice shall be included in
#    all copies or substantial portions of the Software.
#
#    THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
#    IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
#    FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
#    AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
#    LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
#    OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
#    THE SOFTWARE.

import urllib2
import shutil
import json

fip_host = 'http://www.fipradio.fr'
fip_url = fip_host + '/livemeta'

def save_picture(pic_url, filename):
    print("Saving from {} to {}".format(pic_url, filename))

    pic_handler = urllib2.urlopen(pic_url)
    if pic_handler.getcode() == 200:
        print("Content-Type: {}".format(pic_handler.headers.getheader('content-type')))
        print("Content-Length: {}".format(pic_handler.headers.getheader('content-length')))
        with open(filename, 'wb') as fp:
            shutil.copyfileobj(pic_handler, fp)
    else:
        print("Picture HTTP Code: {}".format(pic_handler.getcode()))



handler = urllib2.urlopen(fip_url)

if handler.getcode() == 200:
    data = handler.read().decode("utf-8")
    js = json.loads(data)

    levels = js['levels']
    steps = [level["items"][level["position"]] for level in levels]

    for step in steps:
        if "visual" in js['steps'][step]:
            picture_url = js['steps'][step]["visual"]

            save_picture(picture_url, "{}.jpg".format(step))

else:
    print("HTTP Code: {}".format(handler.getcode()))

