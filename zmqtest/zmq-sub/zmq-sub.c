#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <zmq.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>


#define NUM_FRAMES_PER_ZMQ_MESSAGE 4

struct zmq_dab_message_t
{
    uint32_t version;
    int16_t  buflen[NUM_FRAMES_PER_ZMQ_MESSAGE];
    uint8_t  buf[NUM_FRAMES_PER_ZMQ_MESSAGE*6144];
};


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

    while (1) {
        uint8_t* eti_p = eti;

        memset(eti, 0x55, framelen);
        rc = zmq_recv(sock, &message, framelen, 0);

        fprintf(stderr, "rc=%d \n", rc);

        if (rc > 0 && message.version == 1) {
            uint8_t* buf = message.buf;

            for (int i = 0; i < NUM_FRAMES_PER_ZMQ_MESSAGE; i++) {
                memcpy(eti_p, buf, message.buflen[i]);
                eti_p += 6144;
                buf   += message.buflen[i];
            }

            write(STDOUT_FILENO, eti, framelen);
        }
        else if (rc < 0) {
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

