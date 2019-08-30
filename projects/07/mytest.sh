#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

WORK_DIR=$DIR/test_dir
rm -rf $WORK_DIR
mkdir $WORK_DIR
find . -type f -regex ".*/.*\.\(vm\|tst\|cmp\)" -exec cp {} $WORK_DIR/ \;

SUCC=0
FAIL=0

for i in $WORK_DIR/*.vm;
do
	name=`basename $i .vm`
  echo "Translating $i"
	$DIR/VMtranslator $i $*
	execOut=$(CPUEmulator.sh $WORK_DIR/$name.tst)

  if [[ $execOut == "" ]]  # on fail, no success msg is printed to stdout
  then
      FAIL=$((FAIL+1))
  else
      SUCC=$((SUCC+1))
  fi;

done;

echo "Success count: $SUCC"
echo "Fail count: $FAIL"

exit $FAIL
