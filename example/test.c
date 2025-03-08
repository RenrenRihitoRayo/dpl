#include <stdio.h>

/*
    fflush is manually called,
    it seems that the python stdout
    is not the same as the stdio libraries stdout
    at least to my knowledge.
*/

char* hello() {
    printf("Hello from C!\n");
    fflush(stdout); // manually call this
    return "test";
}

void print_this(char *text) {
    printf("%s\n", text);
    fflush(stdout);
}