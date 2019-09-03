#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

WORK_DIR=$DIR/test_dir
rm -rf $WORK_DIR
mkdir $WORK_DIR
find $DIR/test_src -type f -regex ".*/.*\.\(vm\|tst\|cmp\)" -exec cp {} $WORK_DIR/ \;

rm -rf $WORK_DIR/programs
mkdir $WORK_DIR/programs
cp -r $DIR/test_programs_dir/* $WORK_DIR/programs

SUCC=0
FAIL=0

# Testing .VM files(ex7 and some of ex8)
for i in $WORK_DIR/*.vm;
do
	name=`basename $i .vm`
  echo "Testing .vm file $i"
	$DIR/VMtranslator7 $i $*
	execOut=$(CPUEmulator.sh $WORK_DIR/$name.tst)

  if [[ $execOut == "" ]]  # on fail, no success msg is printed to stdout
  then
      FAIL=$((FAIL+1))
  else
      SUCC=$((SUCC+1))
  fi;

done;

# Testing .VM programs(that have a directory, a Sys.vm and require bootstrap)
for i in $WORK_DIR/programs/*;
do
    echo "Testing vm program at directory $i"
    $DIR/VMtranslator8 $i $* -b
    for tst in $i/*.tst;
    do
        if [[ $tst =~ "VME" ]]
        then
            continue
        fi;
        execOut=$(CPUEmulator.sh $tst $*)
        if [[ $execOut == "" ]]  # on fail, no success msg is printed to stdout
        then
            FAIL=$((FAIL+1))
        else
            SUCC=$((SUCC+1))
        fi;
    done;
done;

echo "Success count: $SUCC"
echo "Fail count: $FAIL"

exit $FAIL
