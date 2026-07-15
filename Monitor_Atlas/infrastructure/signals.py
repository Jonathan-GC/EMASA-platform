from django.db.models.signals import pre_save
from django.dispatch import receiver
from auditlog.models import LogEntry


@receiver(pre_save, sender=LogEntry)
def add_class_name_to_log_entry(sender, instance, **kwargs):
    if instance.content_type:
        # Get the model class from the content_type
        model_class = instance.content_type.model_class()
        if model_class:
            # Ensure additional_data is initialized
            if instance.additional_data is None:
                instance.additional_data = {}

            # Add the class name to additional_data
            instance.additional_data["class_name"] = model_class.__name__
