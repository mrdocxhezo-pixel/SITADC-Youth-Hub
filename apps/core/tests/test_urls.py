from django.test import SimpleTestCase
from django.urls import resolve, reverse

from apps.core.views import about, home


class TestUrls(SimpleTestCase):
    def test_home_url_resolves(self):
        url = reverse("core:home")
        self.assertEqual(resolve(url).func, home)

    def test_about_url_resolves(self):
        url = reverse("core:about")
        self.assertEqual(resolve(url).func, about)
