"""
Tests for the numbering engine: period keys, token rendering and resolution.
"""

from datetime import date

import pytest

from ..constants import ReferenceModules, SequenceResetPeriod
from ..exceptions import (
    InactiveNumberingSchemeError,
    InvalidNumberingSchemeError,
    MissingNumberingContextError,
)
from ..models import ReferenceNumberScheme
from ..numbering import (
    build_token_map,
    current_period_key,
    fiscal_year_label,
    render_reference,
    resolve_scheme,
)


@pytest.fixture
def scheme(db):
    return ReferenceNumberScheme.objects.create(
        name="Project",
        code="project",
        module=ReferenceModules.PROJECTS,
        record_type="project",
        prefix="PRJ",
        pattern="{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        organization_code="SITADC",
        sequence_length=6,
        start_value=1,
        is_default_for_record_type=True,
        is_default_for_module=True,
    )


def _scheme(
    db,
    *,
    name,
    code,
    prefix,
    pattern="{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
    reset_period=SequenceResetPeriod.NEVER,
    fiscal_start_month=1,
    custom_reset_interval_days=None,
):
    return ReferenceNumberScheme.objects.create(
        name=name,
        code=code,
        module=ReferenceModules.REPORTS,
        record_type=code,
        prefix=prefix,
        pattern=pattern,
        organization_code="SITADC",
        sequence_length=6,
        start_value=1,
        reset_period=reset_period,
        fiscal_start_month=fiscal_start_month,
        custom_reset_interval_days=custom_reset_interval_days,
    )


def test_fiscal_year_label():
    assert fiscal_year_label(2025, 1) == "2025-26"
    assert fiscal_year_label(2030, 7) == "2030-31"


@pytest.mark.django_db
def test_current_period_key_never(scheme):
    assert current_period_key(scheme, date(2026, 5, 3)) == "always"


@pytest.mark.django_db
def test_current_period_key_annually(db):
    s = _scheme(
        db, name="A", code="a", prefix="AAA", reset_period=SequenceResetPeriod.ANNUALLY
    )
    assert current_period_key(s, date(2026, 5, 3)) == "2026"


@pytest.mark.django_db
def test_current_period_key_monthly(db):
    s = _scheme(
        db, name="M", code="m", prefix="MMM", reset_period=SequenceResetPeriod.MONTHLY
    )
    assert current_period_key(s, date(2026, 5, 3)) == "2026-05"


@pytest.mark.django_db
def test_current_period_key_daily(db):
    s = _scheme(
        db, name="D", code="d", prefix="DDD", reset_period=SequenceResetPeriod.DAILY
    )
    assert current_period_key(s, date(2026, 5, 3)) == "2026-05-03"


@pytest.mark.django_db
def test_current_period_key_fiscal(db):
    s = _scheme(
        db,
        name="F",
        code="f",
        prefix="FFF",
        reset_period=SequenceResetPeriod.FISCAL,
        fiscal_start_month=7,
    )
    # July 2026 starts the 2026-27 fiscal year.
    assert current_period_key(s, date(2026, 7, 1)) == "2026-27"
    # June 2026 still belongs to the 2025-26 fiscal year.
    assert current_period_key(s, date(2026, 6, 30)) == "2025-26"


@pytest.mark.django_db
def test_current_period_key_custom(db):
    s = _scheme(
        db,
        name="C",
        code="c",
        prefix="CCC",
        reset_period=SequenceResetPeriod.CUSTOM,
        custom_reset_interval_days=30,
    )
    key = current_period_key(s, date(2026, 5, 3))
    assert key.startswith("c")


@pytest.mark.django_db
def test_current_period_key_custom_requires_interval(db):
    s = _scheme(
        db,
        name="CI",
        code="ci",
        prefix="CCZ",
        reset_period=SequenceResetPeriod.CUSTOM,
    )
    with pytest.raises(InvalidNumberingSchemeError):
        current_period_key(s, date(2026, 5, 3))


def test_build_token_map(scheme):
    values = build_token_map(
        scheme, 5, context={"org": "REG", "when": date(2026, 5, 3)}
    )
    assert values["PREFIX"] == "PRJ"
    assert values["ORG"] == "REG"
    assert values["YEAR"] == "2026"
    assert values["MONTH"] == "05"
    assert values["DAY"] == "03"
    assert values["SEQUENCE"] == "000005"


def test_build_token_map_year_from_context(scheme):
    values = build_token_map(scheme, 5, context={"year": 2025})
    assert values["YEAR"] == "2025"


def test_render_reference(scheme):
    reference = render_reference(scheme, 42, context={"org": "SITADC"})
    assert reference == "PRJ-SITADC-2026-000042"


def test_render_reference_custom_context(scheme):
    reference = render_reference(
        scheme,
        7,
        context={"org": "REG", "unit": "north", "when": date(2025, 12, 31)},
    )
    assert reference == "PRJ-REG-2025-000007"


@pytest.mark.django_db
def test_resolve_scheme_by_record_type(scheme):
    resolved = resolve_scheme(ReferenceModules.PROJECTS, "project")
    assert resolved == scheme


@pytest.mark.django_db
def test_resolve_scheme_by_code(scheme):
    resolved = resolve_scheme(ReferenceModules.PROJECTS, scheme_code="project")
    assert resolved == scheme


@pytest.mark.django_db
def test_resolve_scheme_missing_context(db):
    ReferenceNumberScheme.objects.all().delete()
    with pytest.raises(MissingNumberingContextError):
        resolve_scheme(ReferenceModules.REPORTS, "report")


@pytest.mark.django_db
def test_resolve_scheme_inactive(db, scheme):
    scheme.deactivate()
    with pytest.raises(InactiveNumberingSchemeError):
        resolve_scheme(ReferenceModules.PROJECTS, "project")
    # With require_active disabled the scheme resolves anyway.
    assert (
        resolve_scheme(ReferenceModules.PROJECTS, "project", require_active=False)
        == scheme
    )


@pytest.mark.django_db
def test_resolve_scheme_module_default(db):
    # No record-type default; module default applies.
    ReferenceNumberScheme.objects.all().delete()
    module_default = ReferenceNumberScheme.objects.create(
        name="Doc",
        code="doc",
        module=ReferenceModules.DOCUMENTS,
        record_type="",
        prefix="DOC",
        pattern="{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        is_default_for_module=True,
    )
    resolved = resolve_scheme(ReferenceModules.DOCUMENTS, "doc")
    assert resolved == module_default


@pytest.mark.django_db
def test_resolve_scheme_fallback(db):
    ReferenceNumberScheme.objects.all().delete()
    fallback = ReferenceNumberScheme.objects.create(
        name="Fallback",
        code="fallback",
        module=ReferenceModules.REPORTS,
        record_type="",
        prefix="GEN",
        pattern="{PREFIX}-{ORG}-{YEAR}-{SEQUENCE}",
        is_fallback=True,
    )
    resolved = resolve_scheme(ReferenceModules.REPORTS, "anything")
    assert resolved == fallback
