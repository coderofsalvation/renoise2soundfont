#!/bin/bash
path="$(readlink -f "$(dirname $0)")"
[[ ! -n  $SAMPLERATE ]] && SAMPLERATE=44100
[[ ! -n  $BITRATE    ]] && BITRATE=16

dir2wav(){
  find $1 -type f | while read file; do 
      sox "$file" -D -r $SAMPLERATE -b $BITRATE "${file%.*}.wav"
  done
}

"$@"
