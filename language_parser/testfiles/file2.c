#include <stdio.h>

int fibonacci(int n) {
    int a = 0, b = 1, c, i;
    if (n <= 1)
        return n;
    for (i = 2; i <= n; i++) {
        c = a + b;
        a = b;
        b = c;
    }
    return b;
}

int main() {
    int n = 10;
    printf("Fibonacci Series up to %d terms:\n", n);
    for (int i = 0; i < n; i++)
        printf("%d ", fibonacci(i));
    return 0;
}
