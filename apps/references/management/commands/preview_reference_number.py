"""
Preview the next reference number for a context without consuming it.

Run with::

    python manage.py preview_reference_number --module programs --record-type program

The command resolves the applicable scheme and prints the reference that the
next assignment would produce.  It never writes to the database, so it is safe
to run while sequences are in use.
"""

from django.core.management.base import BaseCommand

from apps.core.exceptions import CoreException
from apps.references import selectors
from apps.references.constants import ReferenceModules


class Command(BaseCommand):
    help = "Preview the next reference number without consuming it."

    def add_arguments(self, parser):
        parser.add_argument(
            "--module",
            required=True,
            choices=ReferenceModules.values,
            help="Module to resolve the scheme for.",
        )
        parser.add_argument(
            "--record-type",
            default="",
            help="Optional record type within the module.",
        )
        parser.add_argument(
            "--scheme",
            default="",
            help="Explicit scheme code to use instead of auto-resolution.",
        )
        parser.add_argument(
            "--year",
            type=int,
            default=None,
            help="Year token to preview; defaults to the current year.",
        )
        parser.add_argument(
            "--org",
            default="",
            help="Organization code token; defaults to the scheme's code.",
        )

    def handle(self, *args, **options):
        verbosity = int(options.get("verbosity", 1))
        context = {"year": options["year"], "org": options["org"] or None}
        try:
            result = selectors.next_reference_number(
                module=options["module"],
                record_type=options["record_type"] or None,
                scheme_code=options["scheme"] or None,
                context=context,
            )
        except CoreException as exc:
            self.stderr.write(self.style.ERROR(str(exc)))
            raise SystemExit(1) from exc

        if verbosity:
            self.stdout.write(
                self.style.SUCCESS(
                    f"Scheme: {result['scheme'].name} "
                    f"({result['scheme'].code or 'no-code'})"
                )
            )
            self.stdout.write(self.style.SUCCESS(f"Next value: {result['next_value']}"))
            self.stdout.write(
                self.style.SUCCESS(f"Reference: {result['reference_number']}")
            )
