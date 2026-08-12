"""Private storage for Organizational Registers attachments.

Register attachments (including confidential and sensitive records) are stored
outside the public media directory and never exposed through a direct URL.
Access is always mediated by permission-checked views.
"""

from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.utils.deconstruct import deconstructible


@deconstructible
class PrivateRegisterStorage(FileSystemStorage):
    """Store register attachments outside public media with no direct URL."""

    def __init__(self):
        super().__init__(location=settings.PRIVATE_MEDIA_ROOT, base_url=None)

    def url(self, name):
        raise ValueError("Private register files do not expose public URLs.")


private_register_storage = PrivateRegisterStorage()
