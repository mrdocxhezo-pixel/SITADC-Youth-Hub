"""Private storage for MEAL evidence, reports, and supporting documents."""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateMealStorage(FileSystemStorage):
    """Store MEAL files outside public media and expose no direct URL."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name):
        raise ValueError("Private MEAL files do not expose public URLs.")


private_meal_storage = PrivateMealStorage()
