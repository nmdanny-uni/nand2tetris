###############################################################################
#
# Makefile for VM translator, project 7
#
# Students:
# Daniel Kerbel, ID ***REMOVED***, daniel.kerbel@mail.huji.ac.il
#
###############################################################################

all:
	chmod a+x VMtranslator

tar:
	mkdir -p ex7out
	mkdir -p ex8out
	tar --transform "s|VMtranslator7|VMtranslator|" -cf ex7out/project7.tar *.py README Makefile VMtranslator7
	tar --transform "s|VMtranslator8|VMtranslator|" -cf ex8out/project8.tar *.py README Makefile VMtranslator8

test:
	python3 -m unittest
	chmod +x ./mytest.sh
	./mytest.sh
