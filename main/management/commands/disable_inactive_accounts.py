from django.core.management.base import BaseCommand
from django.core.mail import send_mail
from django.utils import timezone
from datetime import timedelta
from django.conf import settings
from main.models import JobEngagement, ChefProfile, EmployerProfile


class Command(BaseCommand):
    help = "Warn and disable chef and employer accounts that did not submit testimonies within 7 days of engagement."

    def handle(self, *args, **kwargs):
        now = timezone.now()
        warning_threshold = now - timedelta(days=6)
        disable_threshold = now - timedelta(days=7)

        disabled_chefs = 0
        disabled_employers = 0
        warned_chefs = 0
        warned_employers = 0

        # Filter engaged jobs that are still active
        engagements = JobEngagement.objects.filter(status="engaged", hired_at__isnull=False)

        for engagement in engagements:
            hire_date = engagement.hired_at

            # === SEND WARNING EMAILS AT DAY 6 ===
            if hire_date.date() == warning_threshold.date():
                # Chef warning
                if not engagement.chef_testimony:
                    chef_user = engagement.candidate.user
                    if chef_user.is_active:
                        send_mail(
                            subject="⏰ Testimony Reminder: Submit within 24 hours",
                            message=(
                                f"Dear {chef_user.first_name},\n\n"
                                f"You were hired { (now - hire_date).days } days ago, "
                                f"but you haven’t submitted your testimony yet.\n\n"
                                f"Please submit your testimony within 24 hours to avoid account suspension.\n\n"
                                f"Thank you,\nChefCom Support Team"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[chef_user.email],
                            fail_silently=True,
                        )
                        warned_chefs += 1

                # Employer warning
                if not engagement.employer_testimony:
                    employer_user = engagement.employer
                    if employer_user.is_active:
                        send_mail(
                            subject="⏰ Testimony Reminder: Submit within 24 hours",
                            message=(
                                f"Dear {employer_user.first_name},\n\n"
                                f"You hired a chef { (now - hire_date).days } days ago, "
                                f"but you haven’t submitted your testimony yet.\n\n"
                                f"Please submit your testimony within 24 hours to avoid account suspension.\n\n"
                                f"Thank you,\nChefCom Support Team"
                            ),
                            from_email=settings.DEFAULT_FROM_EMAIL,
                            recipient_list=[employer_user.email],
                            fail_silently=True,
                        )
                        warned_employers += 1

            # === DISABLE AFTER 7 DAYS ===
            if hire_date < disable_threshold:
                # Chef disable
                if not engagement.chef_testimony:
                    chef_profile = ChefProfile.objects.filter(user=engagement.candidate.user).first()
                    if chef_profile and chef_profile.user.is_active:
                        chef_profile.user.is_active = False
                        chef_profile.user.save()
                        disabled_chefs += 1

                # Employer disable
                if not engagement.employer_testimony:
                    employer_profile = EmployerProfile.objects.filter(user=engagement.employer).first()
                    if employer_profile and employer_profile.user.is_active:
                        employer_profile.user.is_active = False
                        employer_profile.user.save()
                        disabled_employers += 1

        # === Summary ===
        self.stdout.write(self.style.SUCCESS(
            f"✅ {warned_chefs} chef(s) and {warned_employers} employer(s) warned, "
            f"{disabled_chefs} chef(s) and {disabled_employers} employer(s) disabled."
        ))
