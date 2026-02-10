import os
import re
from datetime import datetime

# Markdown File Path
import configparser

# Get the project root directory (parent of 'src' directory)
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

# Load Config for optional paths
config = configparser.ConfigParser()
config_path = os.path.join(BASE_DIR, 'config.ini')
config.read(config_path, encoding='utf-8')

# Determine Data Directory
if 'PATHS' in config and 'DATA_DIR' in config['PATHS'] and config['PATHS']['DATA_DIR']:
    DATA_DIR = config['PATHS']['DATA_DIR']
else:
    DATA_DIR = BASE_DIR

MASTER_FILE = os.path.join(DATA_DIR, 'workout_db.md')
LOGS_DIR = os.path.join(DATA_DIR, 'logs')
RECENT_FILE = os.path.join(DATA_DIR, 'recent_workouts.md')

def get_monthly_file_path(date_str):
    """
    Returns the path to the monthly log file based on the date string (YYYY-MM-DD).
    Example: 2026-02-10 -> .../logs/2026-02.md
    """
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        month_str = dt.strftime('%Y-%m')
        return os.path.join(LOGS_DIR, f"{month_str}.md")
    except ValueError:
        # Fallback if date format is weird, though shouldn't happen with valid inputs
        return os.path.join(LOGS_DIR, "unknown_date.md")

def save_log(date_str, content):
    """
    Wrapper to save log to Master file, Monthly file, and Recent file.
    """
    # 1. Save to Master
    success_master = _save_to_file(MASTER_FILE, date_str, content, title="Iron Secretary Workout Log")
    
    # 2. Save to Monthly
    monthly_file = get_monthly_file_path(date_str)
    
    # Ensure logs directory exists
    os.makedirs(os.path.dirname(monthly_file), exist_ok=True)
    
    # Determine title for monthly file (e.g., "Workout Log - 2026-02")
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        month_title = f"Workout Log - {dt.strftime('%Y-%m')}"
    except:
        month_title = "Workout Log"
        
    success_monthly = _save_to_file(monthly_file, date_str, content, title=month_title)
    
    # 3. Save to Recent Workouts (Rolling 7)
    _update_recent_workouts(date_str, content)
    
    return success_master and success_monthly

def overwrite_log(date_str, content):
    """
    Wrapper to overwrite log in Master file, Monthly file, and Recent file.
    """
    # 1. Overwrite in Master
    success_master = _overwrite_in_file(MASTER_FILE, date_str, content, title="Iron Secretary Workout Log")
    
    # 2. Overwrite in Monthly
    monthly_file = get_monthly_file_path(date_str)
    
    # Ensure logs directory exists (just in case)
    os.makedirs(os.path.dirname(monthly_file), exist_ok=True)
    
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        month_title = f"Workout Log - {dt.strftime('%Y-%m')}"
    except:
        month_title = "Workout Log"

    success_monthly = _overwrite_in_file(monthly_file, date_str, content, title=month_title)

    # 3. Overwrite in Recent (Rolling 7)
    # Since _update_recent_workouts handles "add or update", we can reuse it?
    # Actually, we need to be careful. If we just "add", it might duplicate if not handled.
    # But _update_recent_workouts re-builds the list.
    _update_recent_workouts(date_str, content)

    return success_master and success_monthly

def _update_recent_workouts(date_str, content):
    """
    Updates the recent_workouts.md file:
    1. Read all existing entries.
    2. Add or Update the entry for date_str.
    3. Sort all entries by date (descending).
    4. Keep top 7.
    5. Write back to file.
    """
    # Read existing entries
    entries = []
    if os.path.exists(RECENT_FILE):
        with open(RECENT_FILE, 'r', encoding='utf-8') as f:
            file_content = f.read()
            
        # Parse existing entries
        # Regex to split by header "## YYYY-MM-DD"
        # We need to capture the date and the content
        pattern = re.compile(r'^## (\d{4}-\d{2}-\d{2}.*)', re.MULTILINE)
        matches = list(pattern.finditer(file_content))
        
        for i, match in enumerate(matches):
            header = match.group(1) # "2026-02-10 (Monday)"
            
            # Extract pure date for comparison
            date_match = re.match(r'^(\d{4}-\d{2}-\d{2})', header)
            entry_date = date_match.group(1) if date_match else "0000-00-00"
            
            start_idx = match.start() # Start of "## "
            if i + 1 < len(matches):
                end_idx = matches[i+1].start()
            else:
                end_idx = len(file_content)
            
            # Full entry including header
            full_entry = file_content[start_idx:end_idx].strip()
            
            # If this is the date we are updating, SKIP it (we will add the new version later)
            if entry_date == date_str:
                continue
                
            entries.append({'date': entry_date, 'content': full_entry})

    # Prepare new entry
    try:
        dt = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = dt.strftime('%A')
    except:
        day_name = ""
        
    new_header = f"## {date_str} ({day_name})"
    new_full_entry = f"{new_header}\n{content}"
    
    entries.append({'date': date_str, 'content': new_full_entry})
    
    # Sort by date descending
    entries.sort(key=lambda x: x['date'], reverse=True)
    
    # Keep top 7
    recent_entries = entries[:7]
    
    # Write back
    final_content = "# Recent Workouts (Last 7 Days)\n\n"
    for entry in recent_entries:
        final_content += entry['content'] + "\n\n"
        
    with open(RECENT_FILE, 'w', encoding='utf-8') as f:
        f.write(final_content.strip() + "\n")

def check_date_exists(date_str):
    """
    Check if a log for the given date already exists in the Master file.
    """
    if not os.path.exists(MASTER_FILE):
        return False
        
    header_pattern = f"## {date_str}"
    with open(MASTER_FILE, 'r', encoding='utf-8') as f:
        for line in f:
            if line.startswith(header_pattern):
                return True
    return False

def _save_to_file(file_path, date_str, content, title="Workout Log"):
    """
    Internal function: Save a workout log for a specific date to a specific Markdown file.
    - If the date header exists: Appends content to that section.
    - If not: Inserts new section in CHRONOLOGICAL ORDER (Newest -> Oldest).
    """
    
    # 1. Read existing content
    if os.path.exists(file_path):
        with open(file_path, 'r', encoding='utf-8') as f:
            existing_content = f.read()
    else:
        existing_content = f"# {title}\n\n"

    # 2. Prepare header and content
    try:
        current_dt = datetime.strptime(date_str, '%Y-%m-%d')
        day_name = current_dt.strftime('%A')
    except ValueError:
        day_name = ""
        current_dt = datetime.max # Treat invalid dates as very new? Or min. Let's say max to put at top if logic fails.

    header_pattern = f"## {date_str}"
    
    lines = existing_content.splitlines()
    
    # Find if header exists
    header_index = -1
    for i, line in enumerate(lines):
        if line.startswith(header_pattern):
            header_index = i
            break
            
    if header_index != -1:
        # --- CASE A: Header Exists (Append) ---
        insert_index = len(lines)
        for i in range(header_index + 1, len(lines)):
            if lines[i].startswith("## "):
                insert_index = i
                break
        
        new_lines = content.splitlines()
        final_lines = lines[:insert_index] + [""] + new_lines + lines[insert_index:]
        
    else:
        # --- CASE B: Header Does Not Exist (Chronological Insert) ---
        insert_pos = -1
        
        # Regex to capture date from header: "## YYYY-MM-DD"
        date_pattern = re.compile(r'^## (\d{4}-\d{2}-\d{2})')
        
        # Start searching after title (assuming title is at top)
        start_search_index = 0
        if len(lines) > 0 and lines[0].startswith('# '):
             start_search_index = 1
             
        for i in range(start_search_index, len(lines)):
            match = date_pattern.match(lines[i])
            if match:
                found_date_str = match.group(1)
                try:
                    found_dt = datetime.strptime(found_date_str, '%Y-%m-%d')
                    
                    # We want Newest First.
                    # If Current > Found, then Current is NEWER than Found -> Insert Here.
                    if current_dt > found_dt:
                        insert_pos = i
                        break
                except ValueError:
                    continue 
                    
        full_header = f"## {date_str} ({day_name})"
        new_section_lines = [full_header] + content.splitlines() + ["", ""]

        if insert_pos != -1:
            # Insert before older date
            final_lines = lines[:insert_pos] + new_section_lines + lines[insert_pos:]
        else:
            # No older date found (or file empty of dates).
            # Check if there are ANY dates.
            has_dates = False
            for line in lines[start_search_index:]:
                if date_pattern.match(line):
                    has_dates = True
                    break
            
            if has_dates:
                # All dates were newer (so current is oldest), append to end
                final_lines = lines + ["", ""] + new_section_lines
            else:
                # No dates, insert at top (after title)
                insert_pos = 1
                while insert_pos < len(lines) and lines[insert_pos].strip() == "":
                    insert_pos += 1
                final_lines = lines[:insert_pos] + new_section_lines + lines[insert_pos:]

    # 3. Clean up and Write
    final_content = "\n".join(final_lines)
    # Recursively clean newlines (allow max 2)
    final_content = re.sub(r'\n{3,}', '\n\n', final_content).strip() + "\n"

    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(final_content)
        
    return True

def _overwrite_in_file(file_path, date_str, content, title="Workout Log"):
    """
    Internal function: Overwrite the log for the given date in a specific file.
    """
    if not os.path.exists(file_path):
        return _save_to_file(file_path, date_str, content, title=title)
        
    # Read all lines
    with open(file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
        
    header_pattern = f"## {date_str}"
    start_index = -1
    end_index = len(lines)
    
    for i, line in enumerate(lines):
        if line.startswith(header_pattern):
            start_index = i
            continue
        
        if start_index != -1 and line.startswith("## ") and i > start_index:
            end_index = i
            break
            
    if start_index != -1:
        # Remove lines from start_index to end_index
        del lines[start_index:end_index]
        
        # Write back cleaned file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write("".join(lines))
            
    # Now save as new
    return _save_to_file(file_path, date_str, content, title=title)

