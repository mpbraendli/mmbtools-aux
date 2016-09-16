Installation scripts for ODR-mmbTools
=====================================

This folder contains install scripts that simplify the compilation
and installation of the ODR-mmbTools

Debian
------

The *debian.sh* script is designed to be run on debian jessie, and installs

 * UHD
 * the fdk-aac library
 * ODR-mmbTools:
   * ODR-DabMux
   * ODR-DabMod
   * ODR-AudioEnc
   * ODR-PadEnc
   * auxiliary scripts


To use it, you have to:

 1. Install debian on your machine
 1. apt-get install sudo and give your user the right to use sudo
 1. download the script to your home directory
 1. make it executable with chmod +x debian.sh
 1. run it with ./debian.sh


GNURadio LiveCD
---------------

This *gnuradio-livecd.sh* script can be used to install the ODR-mmbTools onto
the ubuntu live system offered by the GNURadio project. The following
explanations were given by Tobias Wallerius:

The most convenient way for me was to use the official GNU Radio Live SDR
Environment (Ubuntu based), as it already contains a full GNU Radio
installation. I used version 2015-0623, but in the meantime 2015-0726 is
available. Download the ISO image of your preference.

I wanted to be able to keep changes while running Linux from the USB drive, so
casper was also a requirement. An easy way to achieve this is to use the
Universal USB Installer to install the GNU Radio Ubuntu Image.

### Installing the GNU Radio Live SDR Environment to a USB drive

 *  Download the GNU Radio Live SDR Environment ISO image
 *  Make sure your USB drive is connected to your machine
 *  Start the Universal USB Installer executable
 *  For Step 1, select "Ubuntu"
 *  Select the ISO image in Step 2 with the Browse button
 *  In Step 3, select your USB drive letter
 *  With Step 4, make sure to enable persistence by selecting a file size for storage
 *  Click Create

After the procedure finishes, you can reboot your machine from the USB drive.

### Installing the ODR-mmbTools

After you have the Ubuntu live system running, download and execute the
*gnuradio-livecd.sh* script:

 *  Make sure your internet connection works
 *  Download the modified gnuradio-livecd.sh install script from this post
 *  Make it executable using chmod +x gnuradio-livecd.sh
 *  On your console, start the install script with ./gnuradio-livecd.sh

