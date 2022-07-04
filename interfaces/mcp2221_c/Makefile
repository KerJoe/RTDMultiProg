# Compatability with Windows command line tools
ifeq ($(OS),Windows_NT)
	RM = cmd /C del /Q /F$1
	LIB_EXT = dll
else # Other POSIX
	RM = rm -f$1
	LIB_EXT  = so
endif

CC = gcc
# Get platform describing 'triplet'
PLATFORM = $(shell ${CC} -dumpmachine)

CFLAGS  = -fPIC
LDFLAGS =
LIBS	= -lusb-1.0

all: main.${PLATFORM}.${shared_ext}

main.${PLATFORM}.${shared_ext}: main.c
	${CC} ${CFLAGS} ${LDFLAGS} -shared -o main.${PLATFORM}.${LIB_EXT} main.c ${LIBS}

clean:
	$(RM) main.o main.*.so main_test


main_test: main.c
	${CC} ${CFLAGS} ${LDFLAGS} -g -o main_test main.c -lusb-1.0
