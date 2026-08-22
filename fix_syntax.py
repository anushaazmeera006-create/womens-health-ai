with open('app.py', 'r') as f:
    lines = f.readlines()

# Fix the broken f-string on lines 218-221
lines[217] = '            set_message("success", f"{cluster[\"emoji\"]} {cluster[\"name\"]} day logged.")\n'
# Remove lines 219-221
lines = lines[:219] + lines[221:]

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Fixed f-string syntax error")
