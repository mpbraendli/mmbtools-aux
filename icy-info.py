#!/usr/bin/python2
#
# This script parses the mplayer standard output and
# extracts ICY info for the mot-encoder.
#
# Usage:
# mplayer <blablabla> | icy-info.py file.dls file-with-default.dls
#
# the file-with-default.dls contains DLS text to be sent when there
# is no ICY info

import re
import select
import sys
import time

# quite long, because it's only a fallback, and you don't
# want to overwrite real ICY info
wait_timeout=600

re_icy = re.compile(r"""ICY Info: StreamTitle='([^']*)'.*""")

if len(sys.argv) < 3:
    print("Please specify dls output file, and file containing default text")
    sys.exit(1)

dls_file = sys.argv[1]

default_textfile = sys.argv[2]

def new_dlstext(text):
    if text.strip() == "":
        try:
            fd = open(default_textfile, "r")
            text = fd.read().strip()
            fd.close()
        except Exception as e:
            print("Could not read default text from {}: {}".format(default_textfile, e))

    print("New Text: {}".format(text))

    fd = open(dls_file, "w")
    fd.write(text)
    fd.close()


while True:
    rfds, wfds, efds = select.select( [sys.stdin], [], [], wait_timeout)

    if rfds:
        # new data available on stdin
        new_data = sys.stdin.readline()

        if not new_data:
            break

        match = re_icy.match(new_data)

        if match:
            artist_title = match.groups()[0]
            new_dlstext(artist_title)
        else:
            print("{}".format(new_data.strip()))

    else:
        # timeout reading stdin
        new_dlstext("")

    time.sleep(.1)


