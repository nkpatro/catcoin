#!/bin/bash
# create multiresolution windows icon
ICON_SRC=../../src/qt/res/icons/litecoin.png
ICON_DST=../../src/qt/res/icons/litecoin.ico
convert ${ICON_SRC} -resize 16x16 litecoin-16.png
convert ${ICON_SRC} -resize 32x32 litecoin-32.png
convert ${ICON_SRC} -resize 48x48 litecoin-48.png
convert litecoin-16.png litcoin-32.png litecoin-48.png ${ICON_DST}

