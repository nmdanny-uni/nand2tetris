###############################################################################
#
# Makefile for Jack analyzer & compiler, exercises 10 and 11
#
# Students:
# Daniel Kerbel, ID ***REMOVED***, daniel.kerbel@mail.huji.ac.il
#
###############################################################################

all:
	chmod a+x JackAnalyzer
	chmod a+x JackCompiler

tar:
	tar -cf project10.tar *.py README Makefile JackCompiler JackAnalyzer
	cp project10.tar project11.tar

test:
	python3 -m unittest
	chmod +x ./mytest.sh
	./mytest.sh
