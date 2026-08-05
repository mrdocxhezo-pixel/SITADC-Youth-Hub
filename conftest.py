import pytest
from django.test.client import store_rendered_templates  # type: ignore[attr-defined]
from django.test.signals import template_rendered


@pytest.fixture(autouse=True)
def disconnect_template_rendered_signal():
    template_rendered.disconnect(store_rendered_templates)
    yield
    template_rendered.connect(store_rendered_templates)
