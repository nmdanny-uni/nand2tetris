#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
RC=0
WORK_DIR=`mktemp -d -p $DIR test_temp_dir_XXXXXX`

find . -maxdepth 2 -name '*.asm' -exec cp {} $WORK_DIR/ \;
mkdir $WORK_DIR/{expected,gotten}

for i in $WORK_DIR/*.asm;
do
	name=`basename $i .asm`
	$DIR/Assembler $i
	mv $WORK_DIR/$name.hack $WORK_DIR/gotten/
	Assembler.sh $i
	mv $WORK_DIR/$name.hack $WORK_DIR/expected/

	diff=$(diff -w $WORK_DIR/expected/$name.hack $WORK_DIR/gotten/$name.hack)
	if [ "$diff" != "" ]
	then
		RC=1
		echo "The expected and gotten machine-code for $i don't match"
	fi
done;
rm -rf $WORK_DIR
exit $RC
