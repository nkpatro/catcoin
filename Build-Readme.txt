Start here:

https://github.com/litecoin-project/litecoin/blob/master/doc/build-unix.md


The Positive build instructions are insufficient for Windows.

First be sure you have dos2unix because several of the problems relate to line endings.

In particular to resolve:

AC_CONFIG_MACRO_DIRS([build-aux/m4]) conflicts with ACLOCAL.AMFLAGS=-I build-aux/m4

Do:

find . -name \*.m4|xargs dos2unix
find . -name \*.ac|xargs dos2unix
find . -name \*.am|xargs dos2unix

From:

https://stackoverflow.com/questions/47582762/ac-config-macro-dirsbuild-aux-m4-conflicts-with-aclocal-amflags-i-build-aux

Configure
=========

The ./configure will then fail. You need to do this:

sudo apt install g++
sudo apt install pkg-config
./autogen.sh

After this configure fails again with:

configure: error: openssl  not found.

Tried:
sudo apt-get install libssl-dev

Then we got libevent not found so I am getting the idea the initial big install got smashed so I reran this:

sudo apt-get install build-essential libtool autotools-dev automake pkg-config libssl-dev libevent-dev bsdmainutils python3

Then configure worked.

Make and Make Install
=====================

Make only creates obj

Make install creates executables (I guess) in src folder



