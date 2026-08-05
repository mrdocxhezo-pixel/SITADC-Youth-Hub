import logging

from django.db import transaction

logger = logging.getLogger(__name__)


class BaseService:
    """
    Base service class for business logic operations.
    Encapsulates logic within a single transaction where needed.
    """

    def __init__(self, user=None):
        """
        Optional user context for the service execution
        (e.g. for audit logs/permissions).
        """
        self.user = user

    def execute(self, *args, **kwargs):
        """
        Main execution point for the service.
        Subclasses must implement _execute().
        """
        try:
            with transaction.atomic():
                return self._execute(*args, **kwargs)
        except Exception as e:
            logger.exception(f"Error executing {self.__class__.__name__}: {e!s}")
            raise

    def _execute(self, *args, **kwargs):
        """
        To be implemented by subclasses. Contains the actual business logic.
        """
        raise NotImplementedError("Subclasses must implement _execute()")
