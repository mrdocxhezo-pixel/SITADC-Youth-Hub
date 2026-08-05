import os

from django.core.exceptions import ValidationError
from django.utils.deconstruct import deconstructible
from django.utils.translation import gettext_lazy as _


@deconstructible
class FileSizeValidator:
    """
    Validates that a file's size is not larger than a specified maximum size.
    """

    def __init__(self, max_size_mb: int):
        self.max_size_bytes = max_size_mb * 1024 * 1024
        self.max_size_mb = max_size_mb

    def __call__(self, value):
        if value.size > self.max_size_bytes:
            raise ValidationError(
                _("The maximum file size that can be uploaded is %(max_size)s MB."),
                params={"max_size": self.max_size_mb},
            )


@deconstructible
class FileExtensionValidator:
    """
    Validates that a file has an allowed extension.
    """

    def __init__(self, allowed_extensions):
        self.allowed_extensions = [ext.lower() for ext in allowed_extensions]

    def __call__(self, value):
        extension = os.path.splitext(value.name)[1][1:].lower()
        if extension not in self.allowed_extensions:
            raise ValidationError(
                _("Unsupported file extension. Allowed extensions are: %(allowed)s."),
                params={"allowed": ", ".join(self.allowed_extensions)},
            )
