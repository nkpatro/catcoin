#!/bin/bash

TOPDIR=${TOPDIR:-$(git rev-parse --show-toplevel)}
SRCDIR=${SRCDIR:-$TOPDIR/src}
MANDIR=${MANDIR:-$TOPDIR/doc/man}

VERTEXCOIND=${VERTEXCOIND:-$SRCDIR/vertexcoind}
VERTEXCOINCLI=${VERTEXCOINCLI:-$SRCDIR/vertexcoin-cli}
VERTEXCOINTX=${VERTEXCOINTX:-$SRCDIR/vertexcoin-tx}
VERTEXCOINQT=${VERTEXCOINQT:-$SRCDIR/qt/vertexcoin-qt}

[ ! -x $VERTEXCOIND ] && echo "$VERTEXCOIND not found or not executable." && exit 1

# The autodetected version git tag can screw up manpage output a little bit
VERXVER=($($VERTEXCOINCLI --version | head -n1 | awk -F'[ -]' '{ print $6, $7 }'))

# Create a footer file with copyright content.
# This gets autodetected fine for bitcoind if --version-string is not set,
# but has different outcomes for bitcoin-qt and bitcoin-cli.
echo "[COPYRIGHT]" > footer.h2m
$VERTEXCOIND --version | sed -n '1!p' >> footer.h2m

for cmd in $VERTEXCOIND $VERTEXCOINCLI $VERTEXCOINTX $VERTEXCOINQT; do
  cmdname="${cmd##*/}"
  help2man -N --version-string=${VERXVER[0]} --include=footer.h2m -o ${MANDIR}/${cmdname}.1 ${cmd}
  sed -i "s/\\\-${VERXVER[1]}//g" ${MANDIR}/${cmdname}.1
done

rm -f footer.h2m