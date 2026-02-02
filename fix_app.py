# Read backup and find where it broke
with open('app.py.backup', 'r') as f:
    lines = f.readlines()

# Find the sequential C99 checking code (before I added parallel)
# Line ~400-475 should have the working C99 check loop

# Extract lines 1-491 (before keyword mode)
working_lines = lines[:491]

# Add proper keyword mode block (skip for now - C99 only tool)
working_lines.append("        # Skip keyword mode - C99 only\n")
working_lines.append("        pass\n")
working_lines.append("\n")

# Add the rest (sort, excel, etc.) - start from line ~600
# Find where sort happens
for i, line in enumerate(lines[600:], 600):
    if 'found_domains.sort' in line:
        print(f"Found sort at line {i}")
        working_lines.extend(lines[i:])
        break

with open('app_fixed.py', 'w') as f:
    f.writelines(working_lines)

print("Created app_fixed.py")
