"""Private storage for stakeholder images, evidence, and agreements."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateStakeholderStorage(FileSystemStorage):
    """Store stakeholder files outside public media and expose no direct URL."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name):
        raise ValueError("Private stakeholder files do not expose public URLs.")


private_stakeholder_storage = PrivateStakeholderStorage()
