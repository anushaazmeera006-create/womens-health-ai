with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix all the bracket issues in the questionnaire_steps structure
# Remove extra closing brackets and fix the structure
lines[295] = '                    ]}\n'
lines[296] = '                },\n'
lines[307] = '                    ]}\n'
lines[308] = '                }\n'
lines[309] = '            ]\n'
lines[310] = '        },\n'
lines[311] = '        {\n'
lines[312] = '            "id": "cycle_irregularity",\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed all bracket structure issues")
