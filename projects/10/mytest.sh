#!/bin/bash

DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# folder containing presupplied XML files
CMP_DIR=$DIR/test_src

# setup the temporary tests work directory, fill it with jack files
WORK_DIR=$DIR/test_tempdir
rm -rf $WORK_DIR
cp -r $CMP_DIR $WORK_DIR
find $WORK_DIR/ -name "*.xml" -type f -delete


SUCC=0
FAIL=0



# Testing XML output for folders with jack files
for i in $WORK_DIR/*;
do
  jackFolder=`basename $i`
  echo "Testing .jack folder $jackFolder"
	$DIR/JackAnalyzer $i $*
  for xmlPath in $i/*.xml;
  do
      xml=`basename $xmlPath .xml`
      myXml=$CMP_DIR/$jackFolder/$xml.xml
      echo "   Comparing $xml"
      execOut=$(diff -w $xmlPath $myXml)
      if [[ $execOut == "" ]]  # on success, diff should be empty
      then
          SUCC=$((SUCC+1))
      else
          echo "Failed when testing $xml: diff mismatch between $xmlPath and $myXml"
          echo "To see the difference, type:"
          echo "diff -w $xmlPath $myXml"
          FAIL=$((FAIL+1))
      fi;

  done;
done;

echo "Success count: $SUCC"
echo "Fail count: $FAIL"

exit $FAIL
