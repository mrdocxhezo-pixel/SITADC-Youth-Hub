import pytest
from django.core.exceptions import ValidationError
from django.core.files.uploadedfile import SimpleUploadedFile

from apps.core.validators import FileExtensionValidator, FileSizeValidator


def test_file_size_validator():
    validator = FileSizeValidator(max_size_mb=1)

    # 500 KB file - should pass
    small_file = SimpleUploadedFile("small.txt", b"a" * (500 * 1024))
    validator(small_file)  # No exception raised

    # 2 MB file - should fail
    large_file = SimpleUploadedFile("large.txt", b"a" * (2 * 1024 * 1024))
    with pytest.raises(ValidationError):
        validator(large_file)


def test_file_extension_validator():
    validator = FileExtensionValidator(allowed_extensions=["pdf", "docx"])

    valid_file = SimpleUploadedFile("doc.pdf", b"content")
    validator(valid_file)  # No exception

    invalid_file = SimpleUploadedFile("script.py", b"print('hello')")
    with pytest.raises(ValidationError):
        validator(invalid_file)
