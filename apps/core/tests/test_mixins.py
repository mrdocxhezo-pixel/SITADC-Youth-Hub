import pytest

from apps.core.mixins import ExportMixin, OwnershipMixin, PermissionMixin


class DummyModel(OwnershipMixin):
    def __init__(self, user=None, created_by=None):
        if user:
            self.user = user
        if created_by:
            self.created_by = created_by


def test_ownership_mixin():
    obj1 = DummyModel(created_by="user1")
    assert obj1.is_owned_by("user1") is True
    assert obj1.is_owned_by("user2") is False

    obj2 = DummyModel(user="user2")
    assert obj2.is_owned_by("user2") is True
    assert obj2.is_owned_by("user1") is False


class DummyPermissionModel(PermissionMixin):
    pass


def test_permission_mixin():
    obj = DummyPermissionModel()
    assert obj.has_object_permission("user", "read") is False


class DummyExportModel(ExportMixin):
    pass


def test_export_mixin():
    obj = DummyExportModel()
    with pytest.raises(NotImplementedError):
        obj.get_export_data()
