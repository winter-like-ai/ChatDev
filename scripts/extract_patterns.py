import re

log_file_path = r"d:\Works\code\winter-like-ai\ChatDev\gitchecker.log"
out_file = r"d:\Works\code\winter-like-ai\ChatDev\patterns_output.txt"

# The user specifically asked for "所有的[2026-31-03 21:51:05 INFO] **[Preprocessing]**模式".
# If they mean just the string literally, then:
# exact_pattern = "[2026-31-03 21:51:05 INFO] **[Preprocessing]**"
# But they said "模式" (pattern). It probably means they want lines matching: [TIMESTAMP INFO] **[StageName]**

pattern = re.compile(r'^(\[\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2} INFO\]) (\*\*(?:\[.*?\]|.*?)\*\*.*|.*? \*\*(?:\[.*?\]|.*?)\*\*.*)')

try:
    with open(log_file_path, 'r', encoding='utf-8') as f:
        lines = f.readlines()
except UnicodeDecodeError:
    with open(log_file_path, 'r', encoding='utf-16') as f:
        lines = f.readlines()

matches = []
for line in lines:
    if line.strip() and ('**[' in line or ']**' in line):
        matches.append(line.strip())

with open(out_file, 'w', encoding='utf-8') as f:
    for m in matches:
        f.write(m + '\n')
