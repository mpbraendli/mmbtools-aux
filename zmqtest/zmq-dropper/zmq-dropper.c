#include <stdio.h>
#include <stdlib.h>
#include <unistd.h>
#include <string.h>
#include <zmq.h>
#include <sys/types.h>
#include <sys/stat.h>
#include <fcntl.h>
#include <errno.h>
#include <signal.h>

/* Forward ZMQ messages from one subscriber to a
 * publisher.
 *
 * Each time a SIGUSR1 is received, one message gets dropped.
 */


#define NUM_FRAMES_PER_ZMQ_MESSAGE 4

static int drop_frames = 0;

void signalHandler(int signum)
{
    if (signum == SIGUSR1) {
        drop_frames++;
        signal(SIGUSR1, signalHandler);
    }
}

void barf()
{
    fprintf(stderr, "Error: %s\n", zmq_strerror(errno));
    exit(1);
}


void usage(char** argv)
{
    fprintf(stderr, "usage:           connect to  publish from\n");
    fprintf(stderr, "    zmq-dropper  host port   port\n");
    exit(1);
}

int main(int argc, char** argv)
{
    int rc;
    char endpoint[256];

#ifdef GIT_VERSION
    fprintf(stderr, "zmq-dropper message dropper. version %s\n", GIT_VERSION);
#else
    fprintf(stderr, "zmq-dropper message dropper. version ?\n");
#endif
    fprintf(stderr, "Send me a SIGUSR1 then I will drop a frame\n\n");

    if (argc < 4) {
        usage(argv);
    }

    char* sub_host = argv[1];
    int   sub_port = atoi(argv[2]);
    int   pub_port = atoi(argv[3]);

    fprintf(stderr, "connecting to tcp://%s:%d\n", sub_host, sub_port);

    void* ctx  = zmq_ctx_new();

    /*********** SUBSCRIBER **********/
    void* sub_sock = zmq_socket(ctx, ZMQ_SUB);

    snprintf(endpoint, 256, "tcp://%s:%d", sub_host, sub_port);

    rc = zmq_connect(sub_sock, endpoint);
    fprintf(stderr, "sub connect %d\n", rc);
    if (rc) barf();

    rc = zmq_setsockopt(sub_sock, ZMQ_SUBSCRIBE, NULL, 0);
    fprintf(stderr, "subscribe %d\n", rc);
    if (rc) barf();



    /*********** PUBLISHER **********/
    void* pub_sock = zmq_socket(ctx, ZMQ_PUB);
    snprintf(endpoint, 256, "tcp://*:%d", pub_port);

    rc = zmq_bind(pub_sock, endpoint);
    fprintf(stderr, "pub bind %d\n", rc);
    if (rc) barf();


    /*********** MAIN LOOP *************/
    signal(SIGUSR1, signalHandler);

    const int framelen = NUM_FRAMES_PER_ZMQ_MESSAGE * 6144;
    uint8_t eti[framelen];


    while (1) {
        rc = zmq_recv(sub_sock, eti, framelen, 0);
        if (rc > 0) {
            if (drop_frames) {
                drop_frames--;
                fprintf(stderr, "Dropped one frame\n");
            }
            else {
                rc = zmq_send(pub_sock, eti, framelen, 0);

                if (rc < 0) {
                    fprintf(stderr, "zmq_send rc=%d\n", rc);
                    barf();
                }
            }
        }
        else if (rc == -1) {
            if (errno == EINTR) {
                fprintf(stderr, "zmq_recv interrupted\n");
            }
            else {
                fprintf(stderr, "zmq_recv rc=%d\n", rc);
                barf();
            }
        }
        else {
            fprintf(stderr, "zmq_recv rc=%d\n", rc);
        }
    }

    zmq_close(sub_sock);
    zmq_close(pub_sock);
    zmq_ctx_destroy(ctx);

    return 0;
}

