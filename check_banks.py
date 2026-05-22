import json

zh = json.load(open(r'C:\FriendAndMe\FriendAndMe\data\question_bank.json', 'r', encoding='utf-8'))
en = json.load(open(r'C:\FriendAndMe\FriendAndMe\data\question_bank_en.json', 'r', encoding='utf-8'))

print("=== Chinese Question Bank ===")
for k, v in zh['levels'].items():
    print(f"  Level {k}: {len(v['questions'])} questions")
total_zh = sum(len(v['questions']) for v in zh['levels'].values())
print(f"  Total: {total_zh}")

print()
print("=== English Question Bank ===")
for k, v in en['levels'].items():
    print(f"  Level {k}: {len(v['questions'])} questions")
total_en = sum(len(v['questions']) for v in en['levels'].values())
print(f"  Total: {total_en}")

print()
print("=== ID Alignment Check ===")
missing = []
for lv in zh['levels']:
    zh_ids = {q['id'] for q in zh['levels'][lv]['questions']}
    en_ids = {q['id'] for q in en['levels'].get(lv, {}).get('questions', [])}
    diff = zh_ids - en_ids
    if diff:
        missing.extend(sorted(diff))
if missing:
    print(f"Chinese IDs missing in English: {missing}")
else:
    print("All IDs aligned perfectly!")
