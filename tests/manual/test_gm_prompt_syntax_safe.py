
import os

file_path = 'src/core/llm/prompts/gm.py'
with open(file_path, 'r') as f:
    content = f.read()

# Mock the dependency
# Create a dummy module prompt base
import sys
from types import ModuleType

dummy_base = ModuleType('src.core.llm.prompts.base')
dummy_base.ONE_NIGHT_WEREWOLF_RULES = "RULES"
sys.modules['src.core.llm.prompts.base'] = dummy_base

# Exec the content to check for syntax errors
exec(content)
print("Formatting check passed: gm.py compiled successfully")
# Access one variable to be sure
print(locals()['GM_COMMENT_SYSTEM_PROMPT'][:50])
