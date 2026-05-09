import os
import json
import re
from datetime import datetime

# Get the issue body passed from GitHub Actions
issue_body = os.environ.get('ISSUE_BODY', '')
json_file = 'shirt_data.json'

def update_tracker():
    # Regex to find standard Markdown image links that GitHub generates when dropping an image
    # Format: ![image name](https://github.com/user-attachments/...)
    img_match = re.search(r'!\[.*?\]\((https://github\.com/user-attachments/.*?)\)', issue_body)
    
    if not img_match:
        print("No image found in the issue body. Aborting update.")
        return
    
    image_url = img_match.group(1)
    
    # Try to extract notes if they exist after the "**2. Notes (Optional):**" section
    notes = "New shirt logged."
    if "**2. Notes (Optional):**" in issue_body:
        notes_part = issue_body.split("**2. Notes (Optional):**")[1].strip()
        if notes_part and not notes_part.startswith("*(e.g.,"):
            notes = notes_part
            
    new_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "image_url": image_url,
        "notes": notes
    }
    
    # Load existing data
    if os.path.exists(json_file):
        with open(json_file, 'r') as f:
            data = json.load(f)
    else:
        data = []
        
    data.append(new_entry)
    
    # Save back to JSON
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print(f"Successfully updated tracker with new image: {image_url}")

if __name__ == "__main__":
    update_tracker()
