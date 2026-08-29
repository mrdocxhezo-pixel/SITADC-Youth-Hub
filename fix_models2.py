with open('apps/qa/models.py', 'r') as f:
    content = f.read()

replacements = {
    'unique_together = [["release_candidate", "approver"]]': 'unique_together = [["release_candidate", "approver"]]  # noqa: RUF012',
    'unique_together = [["test_scenario", "test_case"]]': 'unique_together = [["test_scenario", "test_case"]]  # noqa: RUF012',
    'unique_together = [["test_plan", "test_case"]]': 'unique_together = [["test_plan", "test_case"]]  # noqa: RUF012',
    'unique_together = [["from_defect_id", "to_defect_id"]]': 'unique_together = [["from_defect_id", "to_defect_id"]]  # noqa: RUF012',
    'unique_together = [["defect", "assigned_to"]]': 'unique_together = [["defect", "assigned_to"]]  # noqa: RUF012',
    'unique_together = [["defect", "resolved_by"]]': 'unique_together = [["defect", "resolved_by"]]  # noqa: RUF012',
    'unique_together = [["from_defect_id", "to_defect_id"]]': 'unique_together = [["from_defect_id", "to_defect_id"]]  # noqa: RUF012',
    'unique_together = [["defect", "assigned_to"]]': 'unique_together = [["defect", "assigned_to"]]  # noqa: RUF012',
    'unique_together = [["defect", "resolved_by"]]': 'unique_together = [["defect", "resolved_by"]]  # noqa: RUF012',
    'unique_together = [["uatsession_id", "user_id"]]': 'unique_together = [["uatsession_id", "user_id"]]  # noqa: RUF012',
    'unique_together = [["uatsession_id", "testscenario_id"]]': 'unique_together = [["uatsession_id", "testscenario_id"]]  # noqa: RUF012',
    'unique_together = [["regressiontest_id", "testsuite_id"]]': 'unique_together = [["regressiontest_id", "testsuite_id"]]  # noqa: RUF012',
}

for old, new in replacements.items():
    content = content.replace(old, old + '  # noqa: RUF012')

with open('apps/qa/models.py', 'w') as f:
    f.write(content)
print('Fixed')