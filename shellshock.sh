#!/bin/bash

# shellshock.sh
#
# Runs tests for known shellshock related vulnerabilities.
# Tested on assorted ubuntu and debian versions.
#
#   /Pontus Walck, 2014-09-29

FOUND=0

# TODO: CVE-2014-6277 - attack details not published (2014-09-29)
# TODO: CVE-2014-6278 - potentially VERY BAD. attack details not published (2014-09-29)

# CVE-2014-6271 - original shellshock bug
if ( env x='() { :;}; echo vulnerable' bash -c "echo this is a test" ) 2>&1 | grep -q vulnerable
then
  echo 'VULNERABLE TO CVE-2014-6271 (original shellshock)' >&2
  let FOUND++
fi

# CVE-2014-7169 - first secondary bug, not as bad
if ( cd $(mktemp -d); env X='() { (a)=>\' bash -c "echo date"; [ -f "echo" ] && echo vulnerable; rm *; cd; rmdir $OLDPWD ) 2>&1 | grep -q vulnerable
then
  echo 'VULNERABLE TO CVE-2014-7169 (redirection bug)' >&2
  let FOUND++
fi
  
# CVE-2014-7186 - not really related to shellshock. but should probably be patched.
if ! (exec 2>/dev/null; bash -c 'true <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF <<EOF')
then
  echo 'VULNERABLE TO CVE-2014-7186 (redir stack)' >&2
  let FOUND++
fi

# CVE-2014-7187
if ! ((for x in {1..200} ; do echo "for x$x in ; do :"; done; for x in {1..200} ; do echo done ; done) | bash) &>/dev/null
then
  echo 'VULNERABLE TO CVE-2014-7187 (for loop)' >&2
  let FOUND++
fi

if [ "$FOUND" == 0 ]
then
  echo 'Your bash appears to be clean'
else
  echo
  echo 'Your bash needs patching!' >&2
  exit 1
fi
