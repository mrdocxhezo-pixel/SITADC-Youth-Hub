"""
Validate every reference number scheme and report problems.

Run with::

    python manage.py validate_reference_schemes

The command runs the same model validation as the forms and flags any
scheme whose pattern is not token-valid, whose prefix is malformed, or whose
reset configuration is inconsistent.  It exits non-zero when problems are
found, which is useful in CI.
"""

from django.core.exceptions import ValidationError
from django.core.management.base import BaseCommand

from apps.references.models import ReferenceNumberScheme


class Command(BaseCommand):
    help = "Validate reference number schemes."

    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))
        problems = []

        for scheme in ReferenceNumberScheme.objects.all().iterator():
            try:
                scheme.full_clean(exclude=["created_by", "updated_by"])
            except ValidationError as exc:
                problems.append((scheme, exc))

        if not problems:
            if verbosity:
                self.stdout.write(self.style.SUCCESS("All schemes valid."))
            return

        for scheme, problem in problems:
            self.stderr.write(
                self.style.ERROR(f"[{scheme.code or scheme.name}] {problem.messages}")
            )
        self.stderr.write(
            self.style.ERROR(f"{len(problems)} scheme(s) have validation errors.")
        )
        raise SystemExit(1)
