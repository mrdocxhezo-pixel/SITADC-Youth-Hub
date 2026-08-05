from pathlib import Path
import re

for path in Path("apps").rglob("*.py"):
    content = path.read_text(encoding="utf-8")
    original_content = content

    lines = content.splitlines()
    for i in range(len(lines)):
        # Common corruptions from mypy log injection
        if ']" in supertype "Model"' in lines[i]:
            if "def delete(self, *args, **kwargs) -> None:" in lines[i]:
                lines[i] = "    def delete(self, *args, **kwargs) -> None:"
            elif "objects = OrganizationUnitManager()" in lines[i]:
                lines[i] = "    objects = OrganizationUnitManager()"
        elif (
            '"QuerySet[Any, Any]"]' in lines[i]
            or 'def with_unit(self) -> "QuerySet[Any, Any]"' in lines[i]
        ):
            lines[i] = '    def with_unit(self) -> "QuerySet[Any, Any]":'
        elif 'has no attribute "objects"  [attr-defined]' in lines[i]:
            # This is like: LeadershipAuditRecord.objects.create(\" has no attribute \"objects\"  [attr-defined]
            # We want to replace it with just the original model.objects.create(
            lines[i] = re.sub(
                r"(\w+\.objects\.create\().*?\[attr-defined\]", r"\1", lines[i]
            )

        # Any other leftover trailing strings from mypy:
        if "  [override]" in lines[i]:
            lines[i] = lines[i].split("  [override]")[0].strip()
        if "  [assignment]" in lines[i]:
            lines[i] = lines[i].split("  [assignment]")[0].strip()
        if "  [attr-defined]" in lines[i]:
            lines[i] = lines[i].split("  [attr-defined]")[0].strip()
        if "  [misc]" in lines[i]:
            lines[i] = lines[i].split("  [misc]")[0].strip()

        # specifically fix the classvar assignment ones if they got split
        if 'objects: ClassVar["SoftDeleteManager[' in lines[i]:
            m = re.match(
                r"^(.*objects: ClassVar\[\"SoftDeleteManager\[\w+\]\"\]).*", lines[i]
            )
            if m:
                lines[i] = m.group(1)
        if "def user_has_all_permissions" in lines[i] and "-> bool:" not in lines[i]:
            lines[i] = (
                "def user_has_all_permissions(user: User | None, permission_codes: list[str]) -> bool:"
            )
        if "def user_has_any_permission" in lines[i] and "-> bool:" not in lines[i]:
            lines[i] = (
                "def user_has_any_permission(user: User | None, permission_codes: list[str]) -> bool:"
            )

    content = "\n".join(lines) + "\n"
    if content != original_content:
        path.write_text(content, encoding="utf-8")
