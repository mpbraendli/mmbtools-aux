
all: dabp-decoder

SRCS := main.cpp \
	AACDecoder.h AACDecoder.cpp \
	wavfile.h wavfile.cpp

dabp-decoder: $(SRCS)
	g++ -Wall -std=c++17 -fsanitize=address -lfdk-aac -o dabp-decoder AACDecoder.cpp wavfile.cpp main.cpp
