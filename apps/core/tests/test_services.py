import pytest

from apps.core.services import BaseService


class SuccessService(BaseService):
    def _execute(self, data):
        return data * 2


class FailingService(BaseService):
    def _execute(self, data):
        raise ValueError("Simulated failure")


@pytest.mark.django_db
def test_base_service_success():
    service = SuccessService(user="test_user")
    result = service.execute(5)
    assert result == 10
    assert service.user == "test_user"


@pytest.mark.django_db
def test_base_service_failure():
    service = FailingService()
    with pytest.raises(ValueError, match="Simulated failure"):
        service.execute(5)
