#!/bin/bash
#
# mplayer - jack - jack-stdout - dabplus-enc
# encoder script.
#
# Used to encode webstreams for DAB+, requires
# jackd -d dummy -r 32000
# to be running

printerr() {
    echo -e "\033[01;31m$1\033[0m"
}

printmsg() {
    echo -e "\033[01;32m$1\033[0m"
}

set -u

# check number of arguments
if [[ "$#" < 3 ]] ; then
    echo "Usage $0 url jack-id destination [volume]"
    echo "The volume setting is optional"
    exit 1
fi

if [[ "$#" > 2 ]] ; then
    URL=$1
    ID=$2
    DST=$3
fi

if [[ "$#" == 4 ]] ; then
    VOL=$4
else
    VOL=""
fi

BITRATE=80
RATE=32000

encoderalive=0
mplayerpid=0
encoderpid=0

# The trap for Ctrl-C
sigint_trap() {
    printerr "Got Ctrl-C, killing mplayer and encoder"

    if [[ "$mplayerpid" != "0" ]] ; then
        kill -TERM $mplayerpid
        sleep 2
        kill -KILL $mplayerpid
    fi

    if [[ "$encoderpid" != "0" ]] ; then
        kill -TERM $encoderpid
        sleep 2
        kill -KILL $encoderpid
    fi

    printmsg "Goodbye"
    exit
}

trap sigint_trap SIGINT

while true
do
    mplayer_ok=0

    if [[ "$mplayerpid" == "0" ]] ; then
        if [[ "$VOL" == "" ]] ; then
            mplayer -quiet -af resample=$RATE:0:2 -ao jack:name=$ID $URL &
            mplayerpid=$!
        else
            mplayer -quiet -af resample=$RATE:0:2 -af volume=$VOL -ao jack:name=$ID $URL &
            mplayerpid=$!
        fi

        printmsg "Started mplayer with pid $mplayerpid"

        # give some time to mplayer to set up and
        # wait until port becomes visible
        timeout=10

        while [[ "$mplayer_ok" == "0" ]]
        do
            printmsg "Waiting for mplayer to connect to jack ($timeout)"
            sleep 1
            mplayer_ok=$(jack_lsp $ID:out_0 | wc -l)

            timeout=$(( $timeout - 1))

            if [[ "$timeout" == "0" ]] ; then
                printerr "mplayer doesn't connect to jack !"
                kill $mplayerpid
                break
            fi
        done
    else
        printmsg "No need to start mplayer: $mplayerpid"
    fi

    if [[ "$mplayer_ok" == "1" ]] ; then
        jack-stdout $ID:out_0 $ID:out_1 | \
            dabplus-enc -i /dev/stdin -l \
            -b $BITRATE -r $RATE -f raw -a -o $DST &
        encoderpid=$!
    fi

    printmsg "Started encoder with pid $encoderpid"

    sleep 5

    checkloop=1
    while [[ "$checkloop" == "1" ]]
    do
        sleep 2

        kill -s 0 $mplayerpid
        if [[ "$?" != "0" ]] ; then
            # mplayer died
            # we must kill jack-stdout, because we cannot reconnect it
            # to a new mplayer, since we do not know the jack-stdout name.
            # And it has no cmdline option to set one, Rrrrongntudtjuuu!
            if [[ "$encoderpid" != "0" ]] ; then
                kill -TERM $encoderpid
            fi
            checkloop=0

            # mark as dead
            mplayerpid=0

            printerr "Mplayer died"
        fi

        if [[ "$encoderpid" != "0" ]] ; then
            kill -s 0 $encoderpid
            if [[ "$?" != "0" ]] ; then
                # the encoder died,
                # no need to kill the mplayer, we can reconnect to it

                checkloop=0

                printerr "Encoder died"
            fi
        fi
    done

    sleep 5

done

