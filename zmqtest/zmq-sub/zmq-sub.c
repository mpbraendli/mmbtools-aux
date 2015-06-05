#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <zmq.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <time.h>


#define NUM_FRAMES_PER_ZMQ_MESSAGE 4

struct zmq_dab_message_t
{
    uint32_t version;
    int16_t  buflen[NUM_FRAMES_PER_ZMQ_MESSAGE];
    uint8_t  buf[NUM_FRAMES_PER_ZMQ_MESSAGE*6144];
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


void barf()
{
    fprintf(stderr, "Error: %s\n", zmq_strerror(errno));
    exit(1);
}


void do_subscriber(const char* host, int port)
{
    int rc;

    void* ctx  = zmq_ctx_new();
    void* sock = zmq_socket(ctx, ZMQ_SUB);

    char endpoint[256];
    snprintf(endpoint, 256, "tcp://%s:%d", host, port);

    rc = zmq_connect(sock, endpoint);
    fprintf(stderr, "connect %d\n", rc);
    if (rc) barf();

    rc = zmq_setsockopt(sock, ZMQ_SUBSCRIBE, NULL, 0);
    fprintf(stderr, "subscribe %d\n", rc);
    if (rc) barf();


    const int framelen = NUM_FRAMES_PER_ZMQ_MESSAGE * 6144;
    uint8_t eti[framelen];

    struct zmq_dab_message_t message;

    struct timespec time_start;
    size_t total_size = 0;
    size_t num_frames = 0;
    long last_sec = 0;

    while (1) {
        uint8_t* eti_p = eti;

        memset(eti, 0x55, framelen);
        rc = zmq_recv(sock, &message, framelen, 0);

        if (rc > 0 && message.version == 1) {
            uint8_t* buf = message.buf;

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

            for (int i = 0; i < NUM_FRAMES_PER_ZMQ_MESSAGE; i++) {
                memcpy(eti_p, buf, message.buflen[i]);
                eti_p += 6144;
                buf   += message.buflen[i];

                total_size += message.buflen[i];
                num_frames++;
            }

            write(STDOUT_FILENO, eti, framelen);
        }
        else if (rc < 0) {
            fprintf(stderr, "rc=%d \n", rc);

            barf();
        }
    }

    zmq_close(sock);

    zmq_ctx_destroy(ctx);
}

void usage(char** argv)
{
    fprintf(stderr, "usage: %s host port\n", argv[0]);
    fprintf(stderr, "connects to dabmux ETI output at tcp://host:port using a ZeroMQ sub socket\n");
    fprintf(stderr, "and outputs raw ETI on stdout\n");
    exit(1);
}

int main(int argc, char** argv)
{
#ifdef GIT_VERSION
    fprintf(stderr, "zmq-sub ETI reader version %s\n", GIT_VERSION);
#else
    fprintf(stderr, "zmq-sub ETI reader version ?\n");
#endif

    if (argc < 3) {
        usage(argv);
    }

    char* host = argv[1];
    int port = atoi(argv[2]);

    fprintf(stderr, "connecting to tcp://%s:%d\n", host, port);

    do_subscriber(host, port);

    return 0;
}

