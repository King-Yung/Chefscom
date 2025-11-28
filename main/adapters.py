from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from django.contrib.auth import get_user_model
from main.models import ChefProfile, EmployerProfile  # adjust to your app path

User = get_user_model()

class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def save_user(self, request, sociallogin, form=None):
        user = super().save_user(request, sociallogin, form)

        category = request.GET.get("signup_category") or request.session.get("signup_category")

        if category == "chef":
            ChefProfile.objects.get_or_create(user=user)
        elif category == "employer":
            EmployerProfile.objects.get_or_create(user=user)

        return user
