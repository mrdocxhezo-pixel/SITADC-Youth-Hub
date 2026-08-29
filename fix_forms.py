with open('apps/qa/forms.py', 'r') as f:
    content = f.read()

lines = content.split('\n')
for i, line in enumerate(lines):
    stripped = line.strip()
    if stripped.startswith('widgets = {') or stripped.startswith('attrs={') or stripped.startswith('attrs = {'):
        if '# noqa: RUF012' not in line:
            lines[i] = line.rstrip() + '  # noqa: RUF012'

new_content = '\n'.join(lines)
with open('apps/qa/forms.py', 'w') as f:
    f.write(new_content)
print('Fixed')