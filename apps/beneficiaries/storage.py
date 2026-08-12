"""Private storage for beneficiary documents and media."""

from __future__ import annotations

from django.conf import settings
from django.core.files.storage import FileSystemStorage


class PrivateBeneficiaryStorage(FileSystemStorage):
    """FileSystemStorage rooted outside public media with URL access blocked."""

    def __init__(self, **kwargs):
        kwargs.setdefault("location", settings.PRIVATE_MEDIA_ROOT)
        super().__init__(**kwargs)

    def url(self, name):
        raise ValueError(
            "Private beneficiary files have no public URL; download through a "
            "permission-checked view."
        )


private_beneficiary_storage = PrivateBeneficiaryStorage()
