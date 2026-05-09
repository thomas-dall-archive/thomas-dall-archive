import os
import json
import re
from datetime import datetime

# Get the issue body passed from GitHub Actions
issue_body = os.environ.get('ISSUE_BODY', '')
json_file = 'shirt_data.json'

def update_tracker():
    print("Starting tracker update...")
    
    # --- 1. FIND THE IMAGE URL ---
    # This regex looks for URLs inside src="", inside (), or just raw links
    # It specifically targets the github.com/user-attachments/ domain
    image_pattern = r'(https://github\.com/user-attachments/assets/[a-zA-Z0-9\-\.]+)'
    image_match = re.search(image_pattern, issue_body)
    
    if not image_match:
        print("DEBUG: Issue body received:")
        print(issue_body)
        print("ERROR: Could not find a GitHub attachment URL in the issue.")
        return
    
    image_url = image_match.group(1)
    print(f"Found Image URL: {image_url}")

    # --- 2. EXTRACT AND CLEAN NOTES ---
    notes = "New shirt logged."
    if "**2. Notes (Optional):**" in issue_body:
        # Split by the header and take the second half
        parts = issue_body.split("**2. Notes (Optional):**")
        if len(parts) > 1:
            raw_notes = parts[1].strip()
            # Remove the placeholder hint: *(e.g., "...")*
            clean_notes = re.sub(r'\*\(e\.g\..*?\)', '', raw_notes).strip()
            if clean_notes:
                notes = clean_notes
    
    print(f"Final Notes: {notes}")

    # --- 3. CREATE DATA ENTRY ---
    new_entry = {
        "timestamp": datetime.utcnow().isoformat() + "Z",
        "image_url": image_url,
        "notes": notes
    }
    
    # --- 4. UPDATE JSON DATABASE ---
    data = []
    if os.path.exists(json_file):
        try:
            with open(json_file, 'r') as f:
                data = json.load(f)
        except Exception as e:
            print(f"Warning: Could not read existing JSON ({e}). Starting fresh.")
            data = []
        
    data.append(new_entry)
    
    # Save back to JSON
    with open(json_file, 'w') as f:
        json.dump(data, f, indent=2)
        
    print("SUCCESS: shirt_data.json has been updated.")

if __name__ == "__main__":
    update_tracker()
