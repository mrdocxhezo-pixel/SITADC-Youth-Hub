from django.core.exceptions import ObjectDoesNotExist


def get_object_or_none(model_class, **kwargs):
    """
    Returns an object if it exists, otherwise returns None.
    A safer alternative to get() which raises ObjectDoesNotExist.
    """
    try:
        return model_class.objects.get(**kwargs)
    except ObjectDoesNotExist:
        return None
