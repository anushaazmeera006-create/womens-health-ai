with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the bracket mismatch on line 284
lines[283] = '                    ]\n'
lines[284] = '                },\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed bracket mismatch on line 284")
