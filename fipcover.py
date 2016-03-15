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

from HTMLParser import HTMLParser
import urllib2
import shutil

fip_host = 'http://www.fipradio.fr'
fip_url = fip_host + '/player'

class MyHTMLParser(HTMLParser):
    def __init__(self):
        HTMLParser.__init__(self)
        self.cover = False
        self.picture = False
        self.picture_url = ""

    def handle_starttag(self, tag, attrs):
        if tag == "img" and self.cover:
            self.picture = any(
                len(attr) == 2 and attr[0] == "class" and attr[1] == "picture"
                for attr in attrs)
            if self.picture:
                for attr in attrs:
                    if attr[0] == "src":
                        self.picture_url = attr[1]
        elif tag == "div":
            self.cover = any(
                len(attr) == 2 and attr[0] == "class" and attr[1] == "cover"
                for attr in attrs)
        else:
            self.cover = False


    def handle_endtag(self, tag):
        if self.picture and tag == "img":
            self.picture = False

    def handle_data(self, data):
        if self.picture:
            print("Encountered some data  :", data)

req = urllib2.Request(fip_url)
handler = urllib2.urlopen(req)

if handler.getcode() == 200:
    data = handler.read().decode("utf-8")
    parser = MyHTMLParser()
    parser.feed(data)

    if parser.picture_url:
        _, _, filename = parser.picture_url.rpartition("/")
        pic_url = fip_host + parser.picture_url
        print("Saving from {} to {}".format(pic_url, filename))

        pic_handler = urllib2.urlopen(pic_url)
        if pic_handler.getcode() == 200:
            print("Content-Type: {}".format(pic_handler.headers.getheader('content-type')))
            print("Content-Length: {}".format(pic_handler.headers.getheader('content-length')))
            with open(filename, 'wb') as fp:
                shutil.copyfileobj(pic_handler, fp)
        else:
            print("Picture HTTP Code: {}".format(pic_handler.getcode()))

else:
    print("HTTP Code: {}".format(handler.getcode()))

