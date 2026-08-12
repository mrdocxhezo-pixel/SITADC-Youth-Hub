"""Enterprise Search providers.

Each provider indexes one entity type by delegating queryset scoping to the
source module's fail-closed selectors and rendering a canonical hit.
"""

# Importing the provider modules registers each provider with the registry.
from . import (  # noqa: F401
    beneficiaries,
    documents,
    leadership,
    meal,
    meetings,
    memberships,
    notifications,
    programs,
    registers,
    report_instances,
    reports,
    reviews,
    stakeholders,
    volunteers,
)
from .base import SearchHit, SearchProvider, register, registry  # noqa: F401
