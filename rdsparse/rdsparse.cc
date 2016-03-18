#include <iostream>
#include <iomanip>
#include <fstream>
#include <vector>
#include <deque>
#include "decoder_impl.h"
#include "parser_impl.h"

#define PTY_LOCALE 0

using namespace std;

rds::parser_impl parser(true, true, PTY_LOCALE);
rds::decoder_impl decoder(true, true);

void usage()
{
    std::cerr << "Specify filename" << std::endl;
}

int main(int argc, char **argv)
{
    if (argc == 1) {
        usage();
        return 1;
    }

    ifstream in_fd;
    in_fd.open(argv[1]);

    string temp;
    while (getline(in_fd, temp)) {
        stringstream temp_ss(temp);
        deque<string> elems;

        string item;
        char delim = ' ';
        while (getline(temp_ss, item, delim)) {
            elems.push_front(item);
        }

        vector<int> bytes;
        for (auto s : elems) {
            int byte = stoul(s, nullptr, 16);
            bytes.push_back(byte);
        }

        const int skip_head = 7;
        const int skip_tail = 6;

        if (bytes[0] == 0xFD) {
            int length = bytes[1];

            vector<int> bits;

            if (length > 0) {
#define HEX(a) std::hex << std::setfill('0') << std::setw(2) << long(a) << std::dec

                for (int i = skip_head; i < length+(skip_head - skip_tail); i++) {
                    cerr << " " << HEX(bytes[i]);

                    for (int ix = 0; ix < 8; ix++) {
                        bits.push_back(bytes[i] & (1 << ix) ? 1 : 0);
                    }
                }
                cerr << " len: " << bits.size() << endl;

                decoder.work(bits.size(), &bits[0]);
            }

        }

    }

    return 0;
}

