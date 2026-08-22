with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the broken f-string on line 218
lines[217] = '            set_message("success", f"{cluster[\'emoji\']} {cluster[\'name\']} day logged.")\n'

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed f-string syntax error with single quotes")
