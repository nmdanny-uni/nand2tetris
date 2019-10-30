#!/usr/bin/env bash

sh JackAnalyzer "$1" -vc


RAW_FILE=$(dirname "$1")"/"$(basename "$1" .jack)
echo "raw VM is $RAW_FILE.vm"
echo "jack is $1"

mv "$RAW_FILE".vm "$RAW_FILE"Mine.vm

(exec "JackCompiler.sh" "$1")

vimdiff "$RAW_FILE".vm "$RAW_FILE"Mine.vm

rm "$RAW_FILE".vm "$RAW_FILE"Mine.vm


