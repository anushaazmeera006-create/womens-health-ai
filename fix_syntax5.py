with open('app.py', 'r') as f:
    lines = f.readlines()

# Remove the extra closing bracket on line 284
lines[283] = '                    ]\n'
lines = lines[:284] + lines[285:]

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Removed extra closing bracket on line 284")
