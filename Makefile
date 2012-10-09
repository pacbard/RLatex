# Basic Makefile 

CXX = g++
CXXFLAGS = -Wall -ansi -ggdb # with debug
#CXXFLAGS = -Wall -O2 -ansi # without debug
COMPILE = $(CXX) $(CXXFLAGS) -c
NAME = rlatex


# all is the default target and is called when make is called
# without arguments.

all: $(NAME)

$(NAME): main.o socket.o xmlParser.o urlParser.o
	$(CXX) -o $(NAME) main.o socket.o xmlParser.o urlParser.o
	
main.o: main.cpp login.h socket.o xmlParser.o
	$(COMPILE) -o main.o main.cpp
	
socket.o: socket.cpp socket.h urlParser.cpp urlParser.h xmlParser.h xmlParser.cpp
	$(COMPILE) -o socket.o socket.cpp

xmlParser.o: xmlParser.cpp xmlParser.h
	$(COMPILE) -o xmlParser.o xmlParser.cpp

urlParser.o: urlParser.cpp urlParser.h
	$(COMPILE) -o urlParser.o urlParser.cpp

clean:
	rm -rf *.o $(NAME) $(NAME2) $(NAME3) 
