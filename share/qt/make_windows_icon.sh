#!/bin/bash
# create multiresolution windows icon
ICON_SRC=../../src/qt/res/icons/fieldcoin.png
ICON_DST=../../src/qt/res/icons/fieldcoin.ico
convert ${ICON_SRC} -resize 16x16 fieldcoin-16.png
convert ${ICON_SRC} -resize 32x32 fieldcoin-32.png
convert ${ICON_SRC} -resize 48x48 fieldcoin-48.png
convert fieldcoin-16.png fieldcoin-32.png fieldcoin-48.png ${ICON_DST}

