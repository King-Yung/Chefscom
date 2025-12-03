from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import JobApplication, NeedChefSubmission

@receiver(post_save, sender=JobApplication)
def update_needchef_status_on_completion(sender, instance, **kwargs):
    

    # Ensure instance has a linked NeedChefSubmission
    if instance.need_chef is None:
        return

    needchef = instance.need_chef

    # Check status (case-insensitive)
    if instance.status.lower() == "completed":
        NeedChefSubmission.objects.filter(pk=needchef.pk).update(status="Completed")
        return

    # If both testimonies exist → mark completed
    if instance.chef_testimony and instance.employer_testimony:
        NeedChefSubmission.objects.filter(pk=needchef.pk).update(status="Completed")
