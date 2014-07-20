#!/bin/bash
#
# Installer script for
# * UHD
# * ODR-mmbTools:
#   * ODR-DabMux
#   * ODR-DabMod
#   * auxiliary scripts
# * the fdk-aac-dabplus package
#
# and all required dependencies for a
# Debian stable system.
#
# Requires: sudo
#
# TODO gnuradio

RED="\e[91m"
GREEN="\e[92m"
NORMAL="\e[0m"

echo
echo "This is the mmbTools installer script for debian"
echo "================================================"
echo
echo "It will install UHD, dabmux, dabmod, fdk-aac-dabplus"
echo "and all prerequisites to your machine."
echo

echo -e $RED
echo "This program will use sudo to install components on your"
echo "system. Please read the script before you execute it, to"
echo "understand what changes it will do to your system !"
echo
echo "There is no undo functionality here !"
echo -e $NORMAL

if [ "$UID" == "0" ]
then
    echo -e $RED
    echo "Do not run this script as root !"
    echo -e $NORMAL
    echo "Install sudo, and run this script as a normal user."
    exit 1
fi

which sudo
if [ "$?" == "0" ]
then
    echo "Press Ctrl-C to abort installation"
    echo "or Enter to proceed"

    read
else
    echo -e $RED
    echo -e "Please install sudo first $NORMAL using"
    echo " apt-get -y install sudo"
    exit 1
fi

# Fail on error
set -e

if [ -d dab ]
then
    echo -e $RED
    echo "ERROR: The dab directory already exists."
    echo -e $NORMAL
    echo "This script assumes a fresh initialisation,"
    echo "if you have already run it and wish to update"
    echo "the existing installation, please do it manually"
    echo "or erase the dab folder first."
    exit 1
fi

echo -e "$GREEN Updating debian package repositories $NORMAL"
sudo apt-get -y update

echo -e "$GREEN Installing essential prerquisites $NORMAL"
# some essential and less essential prerequisistes
sudo apt-get -y install build-essential git wget \
 sox alsa-tools alsa-utils \
 automake libtool mpg123 \
 libasound2 libasound2-dev \
 libmagickwand5 libmagickwand-dev \
 libjack-jackd2-dev jackd2 \
 ncdu vim ntp links cpufrequtils

# this will install boost, cmake and a lot more
sudo apt-get -y build-dep uhd

# stuff to install from source
mkdir dab || exit
cd dab || exit

echo -e "$GREEN Compiling UHD $NORMAL"
git clone http://github.com/EttusResearch/uhd.git
pushd uhd
git checkout release_003_007_000
mkdir build
cd build
cmake ../host
make
sudo make install
popd

echo -e "$GREEN Installing libsodium $NORMAL"
wget http://download.libsodium.org/libsodium/releases/libsodium-0.6.1.tar.gz
tar -f libsodium-0.6.1.tar.gz -x
pushd libsodium-0.6.1
./configure
make
sudo make install
popd

echo -e "$GREEN Installing ZeroMQ $NORMAL"
wget http://download.zeromq.org/zeromq-4.0.4.tar.gz
tar -f zeromq-4.0.4.tar.gz -x
pushd zeromq-4.0.4
./configure
make
sudo make install
popd

echo -e "$GREEN Installing KA9Q libfec $NORMAL"
git clone https://github.com/Opendigitalradio/ka9q-fec.git
pushd ka9q-fec
./bootstrap
./configure
make
sudo make install
popd

echo
echo -e "$GREEN PREREQUISITES INSTALLED $NORMAL"
### END OF PREREQUISITES

echo -e "$GREEN Fetching mmbtools-aux $NORMAL"
git clone https://github.com/mpbraendli/mmbtools-aux.git


echo -e "$GREEN Compiling ODR-DabMux $NORMAL"
git clone https://github.com/Opendigitalradio/ODR-DabMux.git
pushd ODR-DabMux
./bootstrap.sh
./configure --enable-input-zeromq --enable-output-zeromq
make
sudo make install
popd

echo -e "$GREEN Compiling ODR-DabMod $NORMAL"
git clone https://github.com/Opendigitalradio/ODR-DabMod.git
pushd ODR-DabMod
./bootstrap.sh
./configure --enable-input-zeromq --enable-fft-simd --disable-debug --with-debug-malloc=no
make
sudo make install
popd


echo -e "$GREEN Compiling fdk-aac-dabplus $NORMAL"
git clone https://github.com/Opendigitalradio/fdk-aac-dabplus.git
pushd fdk-aac-dabplus
./bootstrap
./configure --enable-jack
make
sudo make install
popd


echo -e "$GREEN Updating ld cache $NORMAL"
# update ld cache
sudo ldconfig

