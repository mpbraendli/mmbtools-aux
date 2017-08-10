#!/bin/sh
#
# This is the munin plugin that connects to
# ./syslog_munin.py and asks for config and/or
# values

if [ "$1" == "" ]; then
    echo "argument expected"
    exit 1
else
    echo $1 | nc 127.0.0.1 51401
fi
