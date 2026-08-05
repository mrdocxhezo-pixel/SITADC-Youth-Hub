from pathlib import Path
import re

for path in Path("apps").rglob("*.py"):
    content = path.read_text(encoding="utf-8")
    original_content = content

    content = re.sub(
        r"(\.objects\.create\()\" has no attribute \"objects\".*?\]", r"\1", content
    )
    content = re.sub(
        r"(def delete\(self, \*args, \*\*kwargs\) -> None:)]\" in supertype \"Model\".*?\]",
        r"\1",
        content,
    )
    content = re.sub(
        r"(objects: ClassVar\[\".*?\"\])]\" in supertype \"Model\".*?\]", r"\1", content
    )
    content = re.sub(
        r"(def with_unit\(self\) -> \"QuerySet\[Any, Any\]\":).*?\]", r"\1", content
    )
    # Also for authorization.py where '-> QuerySet[...]' got mangled
    content = re.sub(r"(-> QuerySet\[.*?\]:).*?\]", r"\1", content)
    content = re.sub(r"(-> frozenset\[str\]:).*?\]", r"\1", content)
    content = re.sub(r"(codes: set\[str\] = set\(\)).*?\]", r"\1", content)
    content = re.sub(
        r"(def user_has_all_permissions\(user: User \| None, permission_codes: list\[str\]\) -> bool:).*?\]",
        r"\1",
        content,
    )
    content = re.sub(
        r"(def user_has_any_permission\(user: User \| None, permission_codes: list\[str\]\) -> bool:).*?\]",
        r"\1",
        content,
    )
    content = re.sub(r"(-> list\[AccessScope\]:).*?\]", r"\1", content)

    if content != original_content:
        path.write_text(content, encoding="utf-8")
