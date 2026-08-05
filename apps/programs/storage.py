"""Private storage for program documents and evidence."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateProgramStorage(FileSystemStorage):
    """Store program files outside public media and expose no direct URL."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name):
        raise ValueError("Private program files do not expose public URLs.")


private_program_storage = PrivateProgramStorage()
