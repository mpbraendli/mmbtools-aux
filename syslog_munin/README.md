Overview
--------

This folder contains a helper tool that
monitors syslog and counts warnings and errors
for munin to plot.

Setup
-----

 # Configure your syslog daemon to send messages from
   local0 (the facility the ODR-mmbTools log to)
   to localhost:51400 over UDP
 # Use supervisord or similar to run the service *syslog_munin.py*
 # Copy *syslog_munin_plugin.sh* to */etc/munin/plugins/*
 # Wait for munin to start graphing

Todo
----

 * Define alert thresholds in the config descriptor.
