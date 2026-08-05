"""
Fix template block tags: endblock names must match their opening block.
The previous script replaced ALL endblock tags with 'endblock dashboard_content'
which broke the title blocks. This script repairs them properly.
"""

import glob
import re


def fix_template(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Track block stack to rename endblock tags correctly
    # Strategy: parse sequentially, match each endblock to the nearest unclosed block
    result = []
    block_stack = []
    i = 0
    pattern = re.compile(r"\{%[-\s]*(block|endblock)(\s+\w+)?[\s-]*%\}")

    last_end = 0
    for m in pattern.finditer(content):
        result.append(content[last_end : m.start()])
        tag = m.group(1).strip()
        name = m.group(2).strip() if m.group(2) else ""

        if tag == "block":
            block_stack.append(name)
            result.append(m.group(0))
        elif tag == "endblock":
            if block_stack:
                opened = block_stack.pop()
                result.append(
                    "{%% endblock %s %%}" % opened if opened else "{% endblock %}"
                )
            else:
                result.append(m.group(0))
        last_end = m.end()

    result.append(content[last_end:])
    fixed = "".join(result)
    # Clean up the %% escapes we used
    fixed = fixed.replace("%%", "%")

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(fixed)
    return fixed != content


dirs = [
    "apps/leadership/templates/leadership",
    "apps/volunteers/templates/volunteers",
]

changed = 0
for d in dirs:
    for f in glob.glob(d + "/*.html"):
        if fix_template(f):
            changed += 1
            print(f"Fixed: {f}")

print(f"\nTotal fixed: {changed} files.")
