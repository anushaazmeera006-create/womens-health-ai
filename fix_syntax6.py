with open('app.py', 'r') as f:
    lines = f.readlines()

# Remove the extra closing bracket on line 284 and fix the structure
lines[283] = '                    ]\n'
lines[284] = '                },\n                {\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed bracket structure on lines 284-285")
