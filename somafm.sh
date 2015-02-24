#!/bin/bash

# Small somafm command line client.
# Pontus Walck, 2015-02-24

# Lists available stations if run with no arguments. If run with
# an argument, assume it is the name of a station and play it. Use
# Ctrl-C to stop listening.


# Figure out terminal width to avoid wrapping lines.
COLUMNS=$(tput cols)

if [ "$1" == "" ]
then
  # Parse station names and descriptions from the soma.fm web page.
  # The descriptions will be cut short if longer than terminal width.
  # Show stations in reverse order of popularity so the most common
  # stations show up last in the terminal.
  
  wget -qO - "http://soma.fm/listen" | \
    awk -F/ '/now-playing\/[^"]*/ && !seen[$0]++ {
               split($0,z,"[\"/]");
               station = z[6];
             }
             /class="descr"/ {
               split($0,z,"[<>]");
               printf("%-15s  %s\n", station, z[3]);
             }' | \
      tac | \
        perl -pe "s/(.{$[ $COLUMNS - 3 ]}).*/\$1.../"
else
  # Show stream title and tag line.
  # Restart the stream if mplayer exits with non zero status.
  # Parse track titles from mplayer output and discard the rest.
  
  wget -qO - "somafm.com/$1" | \
    perl -0ne \
     'print $1, "\n\n" if /<title>\n(?:SomaFM: )?(.*?)(?: Commercial.*?)?\n<\/title>/'
  
  while ! mplayer http://ice.somafm.com/"$1" 2>/dev/null | \
    awk -F"'" '/StreamTitle/ { print strftime("%H:%M:%S", systime()) "  " $2 }'
  do
    sleep 1
  done
fi
