
import os

file_path = 'src/core/llm/prompts/gm.py'
with open(file_path, 'r') as f:
    lines = f.readlines()

# Remove the import line
lines = [l for l in lines if not l.startswith("from .base")]

content = "".join(lines)

# Mock variables the f-strings expect
ONE_NIGHT_WEREWOLF_RULES = "RULES_MOCK"

# Exec the content
exec(content)
print("Formatting check passed: gm.py compiled successfully")
# Access one variable to be sure
print(locals()['GM_COMMENT_SYSTEM_PROMPT'][:50])
