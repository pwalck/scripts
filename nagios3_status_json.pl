#!/usr/bin/perl

# Converts nagios version 3 status.dat to json, outputs on stdout.
#
# /Pontus Walck, 2015-01-22

open LOG, "/var/cache/nagios3/status.dat";

# Enable slurping in paragraph mode, to read status blocks one at a time.
$/ = "";

while (<LOG>)
{
  ($host) = /host_name=(\S+)/ or next;
  
  if (/^hoststatus/m)
  {
    # Extract host info
    %{$data{$host}} = /^\s*(.*?)=([^\n]+)/gm;
  }
  elsif (/^servicestatus/m)
  {
    ($description) = /^\s*service_description=([^\n]+)/m;
    
    # Extract service info
    %{$data{$host}{services}{$description}} = /^\s*(.*?)=([^\n]+)/gm;
  }
}

use JSON;

print to_json(\%data, { pretty => 1, canonical => 1 });
