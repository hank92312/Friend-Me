import re
import sys
sys.stdout.reconfigure(encoding='utf-8')

# Read translation_data.gd
with open(r'C:\FriendAndMe\FriendAndMe\translation_data.gd', 'r', encoding='utf-8') as f:
    td_content = f.read()

# Extract all keys from EN_MAP
keys_in_map = set()
for match in re.finditer(r'^\t"(.+?)":\s*"', td_content, re.MULTILINE):
    keys_in_map.add(match.group(1))

# Read main.gd
with open(r'C:\FriendAndMe\FriendAndMe\main.gd', 'r', encoding='utf-8') as f:
    main_content = f.read()

# Find all tr("...") calls
tr_keys = set()
for match in re.finditer(r'tr\("(.+?)"\)', main_content):
    tr_keys.add(match.group(1))

# Find keys used in tr() but missing from translation_data.gd
missing = sorted(tr_keys - keys_in_map)

print(f"Total keys in EN_MAP: {len(keys_in_map)}")
print(f"Total tr() calls with unique keys: {len(tr_keys)}")
print(f"Missing translations: {len(missing)}")
print()
if missing:
    for k in missing:
        print(f'  MISSING: "{k}"')
else:
    print("All tr() keys have translations!")

# Also find hardcoded Chinese text assigned to .text without tr()
print("\n=== Hardcoded .text assignments (not using tr()) ===")
hardcoded = []
for i, line in enumerate(main_content.split('\n'), 1):
    m = re.search(r'\.text\s*=\s*"([^"]*[\u4e00-\u9fff][^"]*)"', line)
    if m and 'tr(' not in line:
        hardcoded.append((i, m.group(1)))

for line_num, text in hardcoded:
    print(f"  Line {line_num}: \"{text}\"")
print(f"\nTotal hardcoded Chinese: {len(hardcoded)}")
