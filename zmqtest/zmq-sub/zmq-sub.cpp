/*
   Receive ODR-DabMux ZMQ ETI output and write to a file.

   The MIT License (MIT)

   Copyright (c) 2020 Matthias P. Braendli

   Permission is hereby granted, free of charge, to any person obtaining a copy
   of this software and associated documentation files (the "Software"), to deal
   in the Software without restriction, including without limitation the rights
   to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
   copies of the Software, and to permit persons to whom the Software is
   furnished to do so, subject to the following conditions:

   The above copyright notice and this permission notice shall be included in all
   copies or substantial portions of the Software.

   THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
   IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
   FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
   AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
   LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
   OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE
   SOFTWARE.
*/
#include <cstdio>
#include <cstdlib>
#include <cstring>
#include <ctime>
#include <cmath>
#include <iostream>
#include <stdexcept>
#include <vector>
#include <chrono>
#include <unistd.h>
#include <zmq.h>
#include <sys/types.h>
#include <arpa/inet.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <unistd.h>

using namespace std;

#define NUM_FRAMES_PER_ZMQ_MESSAGE 4

struct zmq_dab_message_t
{
    uint32_t version;
    int16_t  buflen[NUM_FRAMES_PER_ZMQ_MESSAGE];
    // Followed by buf
    // Followed by metadata
};

long timespecdiff_ms(struct timespec time, struct timespec oldTime)
{
    long tv_sec;
    long tv_nsec;
    if (time.tv_nsec < oldTime.tv_nsec) {
        tv_sec = time.tv_sec - 1 - oldTime.tv_sec;
        tv_nsec = 1000000000L + time.tv_nsec - oldTime.tv_nsec;
    }
    else {
        tv_sec = time.tv_sec - oldTime.tv_sec;
        tv_nsec = time.tv_nsec - oldTime.tv_nsec;
    }

    return tv_sec * 1000 + tv_nsec / 1000000;
}

static double get_tist_ms(const uint8_t *p /* ETI frame of length 6144 */, uint16_t dlfc)
{
    const int fct = p[4];
    if (dlfc % 250 != fct) {
        cerr << "Frame FCT=" << fct << " does not correspond to DLFC=" << dlfc << endl;
    }

    bool ficf = (p[5] & 0x80) >> 7;
    const int nst = p[5] & 0x7F;
    const int mid = (p[6] & 0x18) >> 3;

    int ficl = 0;
    if (ficf == 0) {
        throw runtime_error("Not FIC in data stream!");
    }
    else if (mid == 3) {
        ficl = 32;
    }
    else {
        ficl = 24;
    }

    vector<uint32_t> sad(nst);
    vector<uint32_t> stl(nst);
    // Loop over STC subchannels:
    for (int i=0; i < nst; i++) {
        // EDI stream index is 1-indexed
        const int edi_stream_id = i + 1;

        uint32_t scid = (p[8 + 4*i] & 0xFC) >> 2;
        sad[i] = (p[8+4*i] & 0x03) * 256 + p[9+4*i];
        uint32_t tpl = (p[10+4*i] & 0xFC) >> 2;
        stl[i] = (p[10+4*i] & 0x03) * 256 + \
                 p[11+4*i];
    }

    uint16_t mnsc = 0;
    std::memcpy(&mnsc, p + 8 + 4*nst, sizeof(uint16_t));

    /*const uint16_t crc1 = p[8 + 4*nst + 2]*256 + \
                          p[8 + 4*nst + 3]; */

    const uint8_t *fic_data = p + 12 + 4*nst;
    size_t fic_length = ficl * 4;

    // loop over MSC subchannels
    int offset = 0;
    for (int i=0; i < nst; i++) {
        const uint8_t *mst_data = (p + 12 + 4*nst + ficf*ficl*4 + offset);
        offset += stl[i] * 8;
    }

    /*
    const uint16_t crc2 = p[12 + 4*nst + ficf*ficl*4 + offset] * 256 + \
                          p[12 + 4*nst + ficf*ficl*4 + offset + 1]; */

    // TIST
    const size_t tist_ix = 12 + 4*nst + ficf*ficl*4 + offset + 4;
    uint32_t tist = (uint32_t)(p[tist_ix]) << 24 |
                    (uint32_t)(p[tist_ix+1]) << 16 |
                    (uint32_t)(p[tist_ix+2]) << 8 |
                    (uint32_t)(p[tist_ix+3]);

    const double pps_offset = (tist & 0xFFFFFF) / 16384.0;
    return pps_offset;
}

enum class output_metadata_id_e {
    // Contains no value, can be used to group fields
    separation_marker = 0,

    // TAI-UTC offset, value is int16_t.
    utc_offset = 1,

    /* EDI Time is the number of SI seconds since 2000-01-01 T 00:00:00 UTC.
     * value is an uint32_t */
    edi_time = 2,

    /* The DLFC field from the EDI TAG deti. value is uint16_t */
    dlfc = 3,
};

// This metadata gets transmitted in the zmq stream
struct metadata_t {
    uint32_t edi_time;
    int16_t utc_offset;
    uint16_t dlfc;
};

static metadata_t get_md_one_frame(uint8_t *buf, size_t size, size_t *consumed_bytes)
{
    size_t remaining = size;
    if (remaining < 3) {
        throw std::runtime_error("Insufficient data");
    }

    metadata_t md;
    bool utc_offset_received = false;
    bool edi_time_received = false;
    bool dlfc_received = false;

    while (remaining) {
        uint8_t id = buf[0];
        uint16_t len = (((uint16_t)buf[1]) << 8) + buf[2];

        if (id == static_cast<uint8_t>(output_metadata_id_e::separation_marker)) {
            if (len != 0) {
                cerr << "Invalid length " << len << " for metadata: separation_marker" << endl;
            }

            if (not utc_offset_received or not edi_time_received or not dlfc_received) {
                throw std::runtime_error("Incomplete metadata received");
            }

            remaining -= 3;
            *consumed_bytes = size - remaining;
            return md;
        }
        else if (id == static_cast<uint8_t>(output_metadata_id_e::utc_offset)) {
            if (len != 2) {
                cerr << "Invalid length " << len << " for metadata: utc_offset" << endl;
            }
            if (remaining < 2) {
                throw std::runtime_error("Insufficient data for utc_offset");
            }
            uint16_t utco;
            std::memcpy(&utco, buf + 3, sizeof(utco));
            md.utc_offset = ntohs(utco);
            utc_offset_received = true;
            remaining -= 5;
            buf += 5;
        }
        else if (id == static_cast<uint8_t>(output_metadata_id_e::edi_time)) {
            if (len != 4) {
                cerr << "Invalid length " << len << " for metadata: edi_time" << endl;
            }
            if (remaining < 4) {
                throw std::runtime_error("Insufficient data for edi_time");
            }
            uint32_t edi_time;
            std::memcpy(&edi_time, buf + 3, sizeof(edi_time));
            md.edi_time = ntohl(edi_time);
            edi_time_received = true;
            remaining -= 7;
            buf += 7;
        }
        else if (id == static_cast<uint8_t>(output_metadata_id_e::dlfc)) {
            if (len != 2) {
                cerr << "Invalid length " << len << " for metadata: dlfc" << endl;
            }
            if (remaining < 2) {
                throw std::runtime_error("Insufficient data for dlfc");
            }
            uint16_t dlfc;
            std::memcpy(&dlfc, buf + 3, sizeof(dlfc));
            md.dlfc = ntohs(dlfc);
            dlfc_received = true;
            remaining -= 5;
            buf += 5;
        }
    }

    throw std::runtime_error("Insufficient data");
}

void barf()
{
    fprintf(stderr, "Error: %s\n", zmq_strerror(errno));
    exit(1);
}


void do_subscriber(const char* host, int port, bool show_tist)
{
    ssize_t rc;

    void* ctx  = zmq_ctx_new();
    void* sock = zmq_socket(ctx, ZMQ_SUB);

    char endpoint[256];
    snprintf(endpoint, 256, "tcp://%s:%d", host, port);

    rc = zmq_connect(sock, endpoint);
    fprintf(stderr, "connect %zu\n", rc);
    if (rc) barf();

    rc = zmq_setsockopt(sock, ZMQ_SUBSCRIBE, NULL, 0);
    fprintf(stderr, "subscribe %zu\n", rc);
    if (rc) barf();


    constexpr size_t ETILEN = NUM_FRAMES_PER_ZMQ_MESSAGE * 6144;
    uint8_t eti[ETILEN];

    constexpr size_t HEADER_LEN = sizeof(zmq_dab_message_t);
    constexpr size_t MAX_MESSAGE_LEN = HEADER_LEN + ETILEN;
    uint8_t zmq_message[MAX_MESSAGE_LEN];

    struct timespec time_start;
    size_t total_size = 0;
    size_t num_frames = 0;
    long last_sec = 0;

    while (1) {
        uint8_t *eti_p = eti;

        memset(eti, 0x55, ETILEN);
        rc = zmq_recv(sock, zmq_message, MAX_MESSAGE_LEN, 0);

        if (rc < 0) {
            fprintf(stderr, "rc=%zu\n", rc);
            barf();
        }
        else if (rc < (ssize_t)HEADER_LEN) {
            cerr << "Short packet received!" << endl;
            return;
        }

        zmq_dab_message_t message = {};
        memcpy(&message, zmq_message, sizeof(zmq_dab_message_t));

        if (message.version == 1) {
            struct timespec time_now;
            clock_gettime(CLOCK_MONOTONIC, &time_now);

            if (num_frames == 0) {
                time_start.tv_nsec = time_now.tv_nsec;
                time_start.tv_sec  = time_now.tv_sec;
                last_sec = time_now.tv_sec;
            }

            if (time_now.tv_sec > last_sec) {
                last_sec = time_now.tv_sec;

                // calculate time_now - time_start in us
                long diff_ms = timespecdiff_ms(time_now, time_start);

                fprintf(stderr, "Received %zu bytes, %zu ETI frames in %ld milliseconds : %f bytes/second; %f ms/frame\n",
                        total_size, num_frames, diff_ms, 1e3 * total_size/diff_ms,
                        (double)diff_ms/num_frames);
            }

            size_t offset = HEADER_LEN;
            for (int i = 0; i < NUM_FRAMES_PER_ZMQ_MESSAGE; i++) {
                memcpy(eti_p, zmq_message + offset, message.buflen[i]);
                eti_p += 6144;
                offset += message.buflen[i];
                total_size += message.buflen[i];
                num_frames++;
            }

            if (show_tist) {
                for (int i = 0; i < NUM_FRAMES_PER_ZMQ_MESSAGE; i++) {
                    size_t consumed_bytes = 0;

                    auto md = get_md_one_frame(
                            zmq_message + offset,
                            MAX_MESSAGE_LEN - offset,
                            &consumed_bytes);

                    const uint8_t *eti_frame = eti + i * 6144;

                    double pps_offset = get_tist_ms(eti_frame, md.dlfc);

                    using namespace std::chrono;
                    std::time_t posix_timestamp_1_jan_2000 = 946684800;

                    const auto t_frame =
                        system_clock::from_time_t(md.edi_time + posix_timestamp_1_jan_2000 - md.utc_offset) +
                        milliseconds(std::lrint(pps_offset));

                    const auto t_now = system_clock::now();
                    const auto delta = t_frame - t_now;

                    fprintf(stderr, "Metadata: DLFC=%5d UTCO=%3d EDI_TIME=%10d, TIST %3ld ms, t_frame= %ld, Delta=%ld ms\n",
                            md.dlfc, md.utc_offset, md.edi_time, std::lrint(pps_offset),
                            md.edi_time + posix_timestamp_1_jan_2000 - md.utc_offset,
                            duration_cast<milliseconds>(delta).count());

                    offset += consumed_bytes;
                }
            }

            write(STDOUT_FILENO, eti, ETILEN);
        }
        else {
            cerr << "Wrong ZMQ message version!" << endl;
            return;
        }
    }

    zmq_close(sock);

    zmq_ctx_destroy(ctx);
}

void usage(char** argv)
{
    fprintf(stderr, "usage: %s [-t] host port\n", argv[0]);
    fprintf(stderr, "connects to odr-dabmux' ETI output at tcp://host:port using a ZeroMQ sub socket\n");
    fprintf(stderr, "and outputs raw ETI on stdout\n\n");
    fprintf(stderr, "Options:\n");
    fprintf(stderr, " -t : enables TIST decoding and time delta calculation\n");
    exit(1);
}

int main(int argc, char** argv)
{
#ifdef GIT_VERSION
    fprintf(stderr, "zmq-sub ETI reader version %s\n", GIT_VERSION);
#else
    fprintf(stderr, "zmq-sub ETI reader version ?\n");
#endif

    int flags = 0;
    bool show_tist = false;
    int opt;
    while ((opt = getopt(argc, argv, "t")) != -1) {
        switch (opt) {
            case 't':
                show_tist = true;
                break;
            default:
                fprintf(stderr, "Invalid option\n");
                usage(argv);
        }
    }

    if (optind + 1 >= argc) {
        fprintf(stderr, "Missing host and port\n");
        usage(argv);
    }

    char *host = argv[optind];
    int port = atoi(argv[optind + 1]);

    fprintf(stderr, "connecting to tcp://%s:%d, show tist=%s\n", host, port, show_tist ? "true" : "false");

    try {
        do_subscriber(host, port, show_tist);
    }
    catch (const std::runtime_error &e) {
        cerr << "Runtime error: " << e.what() << endl;
    }
    catch (const std::logic_error &e) {
        cerr << "Logic error! " << e.what() << endl;
    }

    return 0;
}

