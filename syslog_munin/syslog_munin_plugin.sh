#!/bin/sh
#
# This is the munin plugin that connects to
# ./syslog_munin.py and asks for config and/or
# values

if [ "$1" == "config" ]; then
    echo config | nc 127.0.0.1 51401
elif [ "$1" == "" ]; then
    echo values | nc 127.0.0.1 51401
else
    exit 1
fi
