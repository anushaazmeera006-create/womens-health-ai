with open('app.py', 'r') as f:
    lines = f.readlines()

# Remove the problematic line 219
lines = lines[:218] + lines[219:]

with open('app.py', 'w') as f:
    f.writelines(lines)

print("Removed problematic line 219")
