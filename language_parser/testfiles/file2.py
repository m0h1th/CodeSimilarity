def fibonacci(n):
    s = 0
    t = 1
    for i in range(n):
        s, t = t, s + t
    return s