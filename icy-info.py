#!/usr/bin/python2
#
# Pipe mplayer into this script

import re
import sys

re_icy = re.compile(r"""ICY Info: StreamTitle='([^']*)'.*""")

if len(sys.argv) < 3:
    print("Please specify dls output file, and default text")
    sys.exit(1)

dls_file = sys.argv[1]

default_text = sys.argv[2]

while True:
    new_data = sys.stdin.readline()

    match = re_icy.match(new_data)

    if match:
        artist_title = match.groups()[0]

        if artist_title.strip() == "":
            artist_title = default_text

        print("New artist: {}".format(artist_title))

        fd = open(dls_file, "w")
        fd.write(artist_title)
        fd.close()
    else:
        print("{}".format(new_data.strip()))


