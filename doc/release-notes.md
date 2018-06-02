0.8.7.5 changes
=============
- openssl-1.0.1k or older versions patched for CVE-2014-8275 broke compatibility with Bitcoin and Hypercoin.
  This update patches Hypercoin to maintain compatibility with CVE-2014-8275 patched openssl.
- If you are running v0.8.7.4 as distributed by hypercoin.org you do not need to upgrade.
  The binaries distributed on hypercoin.org contain their own copy of openssl so they are unaffected by this issue.
