import re
import os

files = ["apps/leadership/views.py", "apps/volunteers/views.py"]

for f in files:
    with open(f, "r") as file:
        content = file.read()

    # In leadership views, we mistakenly replaced "leadership.view_leadershipprofile" with "LEADERSHIP_VIEW
    content = content.replace('"LEADERSHIP_VIEW', "LEADERSHIP_VIEW")
    content = content.replace('"LEADERSHIP_CREATE', "LEADERSHIP_CREATE")
    content = content.replace('"LEADERSHIP_UPDATE', "LEADERSHIP_UPDATE")

    # We also need to add imports to apps/leadership/views.py
    if f == "apps/leadership/views.py" and "from .permissions import" not in content:
        import_stmt = "from .permissions import LEADERSHIP_VIEW, LEADERSHIP_CREATE, LEADERSHIP_UPDATE, LEADERSHIP_ASSIGN\n"
        content = content.replace(
            "from apps.rbac.mixins import PermissionRequiredMixin\n",
            "from apps.rbac.mixins import PermissionRequiredMixin\n" + import_stmt,
        )

    with open(f, "w") as file:
        file.write(content)
