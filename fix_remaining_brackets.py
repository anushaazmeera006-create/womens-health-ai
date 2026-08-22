with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the bracket issues:
# Remove extra closing bracket on line 296
# Fix the structure on lines 308-310
lines[295] = '                    ]}\n'
lines[296] = '                },\n'
lines[307] = '                    ]}\n'
lines[308] = '                }\n'
lines[309] = '            ]\n'
lines[310] = '        },\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed remaining bracket issues")
