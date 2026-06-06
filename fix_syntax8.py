with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the bracket structure on lines 296-298
lines[295] = '                    ]}\n'
lines[296] = '                },\n'
lines[297] = '                {\n'
lines[298] = '                    "id": "height",\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed bracket structure and added missing id field")
