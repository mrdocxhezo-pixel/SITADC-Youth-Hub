with open('apps/qa/models.py', 'r') as f:
    content = f.read()

# Fix the broken lines
replacements = {
    'ordering = [  # noqa: RUF012"name"]': 'ordering = ["name"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-created_at"]': 'ordering = ["-created_at"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"environment_type", "name"]': 'ordering = ["environment_type", "name"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"test_plan", "order", "name"]': 'ordering = ["test_plan", "order", "name"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"test_suite", "test_id"]': 'ordering = ["test_suite", "test_id"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"test_plan", "name"]': 'ordering = ["test_plan", "name"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"order"]': 'ordering = ["order"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-started_at"]': 'ordering = ["-started_at"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"execution", "step_number"]': 'ordering = ["execution", "step_number"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-created_at"]': 'ordering = ["-created_at"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-assigned_at"]': 'ordering = ["-assigned_at"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-resolved_at"]': 'ordering = ["-resolved_at"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-period_end", "metric_type"]': 'ordering = ["-period_end", "metric_type"]  # noqa: RUF012',
    'ordering = [  # noqa: RUF012"-timestamp"]': 'ordering = ["-timestamp"]  # noqa: RUF012',
}

for old, new in replacements.items():
    content = content.replace(old, new)

with open('apps/qa/models.py', 'w') as f:
    f.write(content)
print('Fixed')