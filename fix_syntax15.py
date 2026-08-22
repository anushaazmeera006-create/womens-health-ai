with open('app.py', 'r') as f:
    lines = f.readlines()

# Remove the extra closing bracket on line 296
lines[295] = '                    ]}\n'
lines[296] = '                },\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Removed extra closing bracket on line 296")
