#!/bin/bash

# Reads stdin to temporary file. If content has changed compared
# to $1, write to $1.
#
# The point is to not update the file mtime, and to not cause
# programs listening for file updates with e.g. inotify to be
# triggered.
#
# Examples:
#  curl -s http://mysite.com/feed.xml | write_if_changed feed.xml
#  find /etc -type f | sort | write_if_changed etc.files

function die
{
  echo "ERROR: $1" >&2
  exit 1
}

if [ "$1" == "-n" ]
then
  non_empty=1
  shift
fi

[ -n "$1" ]   || die "Please give output file argument"
tmp=$(mktemp) || die "Could not create temporary file"
trap 'rm -f "$tmp"' EXIT

cat > "$tmp"

# Skip if non_empty option given and input is empty.
[ "$non_empty" == "1" ] && ! [ -s "$tmp" ] && exit 1

cmp -s "$tmp" "$1" || status="changed"

[ "$status" == "changed" ] && \
  { cat "$tmp" > "$1" || die "Could not write to \"$1\""; }

[ "$status" == "changed" ] || exit 1
