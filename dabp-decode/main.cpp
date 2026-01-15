#include <iostream>
#include <string>
#include <vector>
#include "AACDecoder.h"

int main(int argc, char **argv)
{
    if (argc != 4) {
        std::cerr << "Usage: " << argv[0] << " INFILE FRAME_SIZE OUTFILE\n";
        return 1;
    }

    auto frame_size = std::stol(argv[2]);
    if (frame_size == 0) {
        std::cerr << "Frame size 0 !\n";
        return 1;
    }

    FILE *fd = fopen(argv[1], "r");
    if (fd == nullptr) {
        std::cerr << "Could not open file !\n";
        return 1;
    }

    AACDecoder aacdec(argv[3]);

    std::vector<uint8_t> buf;
    buf.resize(frame_size);

    while (not feof(fd)) {
        if (fread(buf.data(), buf.size(), 1, fd) == 0) {
            std::cerr << "fread 0\n";
            break;
        }

        aacdec.decode_frame(buf.data(), buf.size());
    }

    fclose(fd);

    return 0;
}
