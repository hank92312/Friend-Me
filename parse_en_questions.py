import re
import json

def parse_markdown(md_path):
    with open(md_path, 'r', encoding='utf-8') as f:
        content = f.read()

    levels = {}
    
    # Split content by level headers
    level_sections = re.split(r'^##\s+Level\s+(\d+):\s*(.*?)\s*\((.*?)\)', content, flags=re.MULTILINE)
    
    # The first element in level_sections is the header part of the file (before Level 1)
    # The rest are in groups of 4: level_num, level_name, level_subtitle, level_content
    for i in range(1, len(level_sections), 4):
        level_num = int(level_sections[i].strip())
        level_name = level_sections[i+1].strip()
        level_subtitle = level_sections[i+2].strip()
        level_content = level_sections[i+3]
        
        # Parse description from psychological goal line
        # e.g., *Psychological Goal: Establish basic...*
        desc_match = re.search(r'\*(?:Psychological Goal:\s*)?(.*?)\*', level_content)
        description = desc_match.group(1).strip() if desc_match else ""
        
        # Parse questions
        # e.g., 1. **Breakfast Preference**: If you had to eat...
        questions = []
        q_lines = re.findall(r'^\s*(\d+)\.\s*\*\*(.*?)\*\*:\s*(.*?)\s*$', level_content, re.MULTILINE)
        for q_num_str, q_tag, q_text in q_lines:
            q_num = int(q_num_str)
            q_id = f"L{level_num}Q{q_num:02d}"
            questions.append({
                "id": q_id,
                "tag": q_tag.strip(),
                "text": q_text.strip()
            })
            
        levels[str(level_num)] = {
            "name": level_name,
            "subtitle": level_subtitle,
            "description": description,
            "questions": questions
        }
        
    return {"levels": levels}

def main():
    md_path = r"C:\FriendAndMe\Friends&Me_Question_Bank_english.md"
    json_path = r"C:\FriendAndMe\FriendAndMe\data\question_bank_en.json"
    
    print(f"Parsing {md_path}...")
    data = parse_markdown(md_path)
    
    print(f"Saving to {json_path}...")
    with open(json_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)
        
    # Print statistics
    print("\n--- Statistics ---")
    for lv_num, lv_data in data["levels"].items():
        print(f"Level {lv_num} ({lv_data['name']}): {len(lv_data['questions'])} questions")
    print("------------------\nDone!")

if __name__ == '__main__':
    main()
