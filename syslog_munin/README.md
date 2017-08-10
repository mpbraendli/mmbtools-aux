Overview
--------

This folder contains a helper tool that
monitors syslog and counts warnings and errors
for munin to plot.

Setup
-----

 1. Configure your syslog daemon to send messages from
    local0 (the facility the ODR-mmbTools log to)
    to localhost:51400 over UDP
 1. Use supervisord or similar to run the service *syslog_munin.py*
 1. Copy *syslog_munin_plugin.sh* to */etc/munin/plugins/*
 1. Wait for munin to start graphing

Todo
----

 * Define alert thresholds in the config descriptor.
