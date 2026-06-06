with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the indentation error on line 297
lines[296] = '                },\n'
lines[297] = '                {\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed indentation error on line 297")
