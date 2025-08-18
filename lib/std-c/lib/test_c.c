#include <stdio.h>

void print_greeting(void) {
    printf("Hello, from C!\n");
}

void print_num(int num) {
    printf("Number: %i\n", num);
}

int fib(int n) {
    int a = 1;
    int b = 0;
    int c = 0;
    
    while (n) {
        c = a + b;
        a = b;
        b = c;
        n--;
    }
    return b;
}

int main() {
    printf("fib(10) = %i\n", fib(10));
}