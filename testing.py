def loopi():
    a = int(input("Enter a small number: "))
    b = int(input("Enter a big number: "))
    c = []
    d = []
    while a <= b:
        c.append(a)
        a += 1
    #     d.append(a)
    # c.extend(d)  # Use extend() to concatenate lists
    return c

result = loopi()

print(result)
