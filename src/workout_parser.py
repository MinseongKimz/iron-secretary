import re
from datetime import datetime

class WorkoutParser:
    def __init__(self):
        # Matches patterns like "2/6", "2월 5일", "2026-02-09"
        # 1. MM/DD
        # 2. MM월 DD일
        # 3. YYYY-MM-DD
        self.patterns = [
            r'(\d{1,2})/(\d{1,2})',
            r'(\d{1,2})월\s*(\d{1,2})일',
            r'(\d{4})-(\d{1,2})-(\d{1,2})'
        ]

    def parse_bulk_text(self, text):
        """
        Parses text containing multiple workout logs separated by dates.
        Returns a dictionary: {'YYYY-MM-DD': 'log content'}
        """
        logs = {}
        lines = text.split('\n')
        current_date_str = None
        current_content = []

        year = datetime.now().year  # Assume current year for incomplete dates

        for line in lines:
            line = line.strip()
            date_found = False
            
            # Check for date headers
            for pattern in self.patterns:
                match = re.search(pattern, line)
                if match:
                    # If we found a date, save the previous accumulated content
                    if current_date_str:
                        logs[current_date_str] = "\n".join(current_content).strip()
                        current_content = []

                    # Parse the found date
                    try:
                        if len(match.groups()) == 2:  # MM/DD or MM월 DD일
                            month, day = map(int, match.groups())
                            # Handle potential year wrap if user enters Dec in Jan? Simplified for now.
                            current_date_str = f"{year}-{month:02d}-{day:02d}"
                        elif len(match.groups()) == 3: # YYYY-MM-DD
                            y, m, d = map(int, match.groups())
                            current_date_str = f"{y}-{m:02d}-{d:02d}"
                        
                        date_found = True
                        # Don't add the date line itself to content, or maybe add it as a header?
                        # Let's add it for context if it has other text on the line
                        current_content.append(line) 
                        break 
                    except ValueError:
                        continue # If date parsing fails, treat as normal text

            if not date_found:
                if current_date_str:
                    current_content.append(line)
        
        # Save the last entry
        if current_date_str and current_content:
            logs[current_date_str] = "\n".join(current_content).strip()
            
        return logs

def test_parser():
    sample_text = """
### [13:41:17] 기록
2/6 가슴 삼두

덤벨 풀오버 15kg 12회 4셋
...

### [13:41:28] 기록
2/5 등 이두

어시스트 풀업...
"""
    parser = WorkoutParser()
    parsed = parser.parse_bulk_text(sample_text)
    import json
    print(json.dumps(parsed, indent=2, ensure_ascii=False))

if __name__ == "__main__":
    test_parser()
