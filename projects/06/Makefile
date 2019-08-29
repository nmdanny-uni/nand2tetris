###############################################################################
#
# Makefile for Assembler, project 6
#
# Students:
# Daniel Kerbel, ID ***REMOVED***, daniel.kerbel@mail.huji.ac.il
#
###############################################################################

all:
	chmod a+x Assembler

# As you can see, all it does is grant execution permissions for your run time executable, so your project 
# will be able to run on the graders' computers. In this case, the "all" rule has no preqrequisites.

# A general rule looks like this:
# rule_name: prerequisite1 prerequisite2 prerequisite3 prerequisite4 ...
#	command1
#	command2
#	command3
#	...
# Where each preqrequisite is a rule name, and each command is a command-line command (for example chmod, 
# javac, echo, etc').

test:
	python3 -m unittest
	chmod +x ./mytest.sh
	./mytest.sh
