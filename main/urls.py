from django.urls import path, reverse_lazy
from . import views
from .views import subscription_page, start_subscription, verify_subscription, engage_candidate
from django.contrib.auth import views as auth_views
from .views import reset_password_view, change_password_view
from .views import ask_ai

urlpatterns = [
    # Home
    path("", views.home, name="home"),
    path('api/ask-ai/', ask_ai, name='ask_ai'),

    # Candidate & Employer onboarding
    path("need_job/", views.need_job, name="need_job"),
    path("need_staff/", views.need_staff, name="need_staff"),
    path("candidates/thank_you/", views.thank_you, name="thank_you"),
    path("register/", views.candidate_register, name="candidate_register"),
    path("candidate/success/", views.candidate_register_success, name="candidate_register_success"),
    path("signup/", views.signup, name="signup"),
    path("signup_employer/", views.signup_employer, name="signup_employer"),
    path("login/", views.user_login, name="login"),
    path("set-role/<str:role>/", views.set_role, name="set_role"),
    path("verify-otp/", views.verify_otp_view, name="verify_otp"),
    path("resend-otp/", views.resend_otp_view, name="resend_otp"),
    path("logout/", views.logout_view, name="logout"),
    path("recovery_password/", views.recovery_password, name="recovery_password"),

    # Profile & redirect
    path('complete-profile/', views.complete_profile, name='complete_profile'),
    path('redirect-after-login/', views.redirect_after_login, name='redirect_after_login'),

    # Pages
    path("about/", views.about, name="about"),
    path("candidates/culinary_agents/", views.culinary_agents, name="culinary_agents"),
    path("services/", views.services, name="services"),
    path("team/", views.team, name="team"),
    path("faq/", views.faq, name="faq"),
    path("partners/", views.partners, name="partners"),
    path("contact/", views.contact, name="contact"),
    path("event_news/", views.event_news, name="event_news"),
    path("testimonies/", views.testimonies, name="testimonies"),
    path("chefs_hub/", views.chefs_hub, name="chefs_hub"),
    path("consultancy_services/", views.consultancy_services, name="consultancy_services"),
    path("terms_condition/", views.terms_condition, name="terms_condition"),
    path("privacy_policy/", views.privacy_policy, name="privacy_policy"),
    path("disclaimer/", views.disclaimer, name="disclaimer"),

    # Job / Staff pages
    path("submit_cv/", views.submit_cv, name="submit_cv"),
    path("submit_job/", views.submit_job, name="submit_job"),
    path("employers_list/", views.employers_list, name="employers_list"),
    path("company_detail/", views.company_detail, name="company_detail"),
    path("job_vacancies/", views.job_vacancies, name="job_vacancies"),
    path("relief_chef/", views.relief_chef, name="relief_chef"),
    path("permanent_chef/", views.permanent_chef, name="permanent_chef"),
    path("private_chef/", views.private_chef, name="private_chef"),

    # Verification
    path("verify/", views.verify_code, name="verify_code"),
    path("resend_code/", views.resend_code, name="resend_code"),

    # Dashboards
    path("chef/", views.chef_dashboard, name="chef_dashboard"),
    path("employer/", views.employer_dashboard, name="employer_dashboard"),

    # Subscription
    path("subscription/", subscription_page, name="subscription_page"),
    path("subscription/start/", start_subscription, name="start_subscription"),
    path("subscription/verify/", verify_subscription, name="verify_subscription"),

    # Newsletter
    path("subscribe-newsletter/", views.subscribe_newsletter, name="subscribe_newsletter"),

    # Country/state AJAX
    path("ajax/load-states/", views.load_states, name="load_states"),
    path("candidates/load_states/", views.load_states, name="load_states"),
    path("get_country_code/", views.get_country_code, name="get_country_code"),

    # Job engagements system
    path("engage/", engage_candidate, name="engage_candidate"),
    path("dashboard/job_alerts/", views.job_alerts, name="job_alerts"),
    path("dashboard/applied/", views.applied, name="applied"),
    path("dashboard/manage_chef/", views.manage_chef, name="manage_chef"),
    path("engagement/<int:engagement_id>/accept/", views.accept_engagement, name="accept_engagement"),
    path("engagement/<int:engagement_id>/reject/", views.reject_engagement, name="reject_engagement"),
    path("engagement/<int:engagement_id>/delete/", views.delete_engagement, name="delete_engagement"),
    path("engagement/<int:engagement_id>/engage/", views.mark_engaged, name="mark_engaged"),
    path("engagement/<int:engagement_id>/testimony/", views.submit_testimony, name="submit_testimony"),
    path("engagement/<int:engagement_id>/chef_testimony/", views.submit_testimony, name="submit_chef_testimony"),

    # Applications
    path("dashboard/applications/", views.view_applications, name="view_applications"),
    path("dashboard/my-jobs/", views.manage_applications, name="manage_applications"),

    # Submit testimony
    path("application/<int:application_id>/submit_testimonyy/", views.submit_testimonyy, name="submit_testimonyy"),

    # Application action URLs
    path("application/<int:app_id>/accept/", views.accept_application, name="accept_application"),
    path("application/<int:app_id>/reject/", views.reject_application, name="reject_application"),
    path("application/<int:app_id>/hire/", views.hire_application, name="hire_application"),
    path("application/<int:app_id>/delete/", views.delete_application, name="delete_application"),

    # Apply for jobs / need-staff
    path('apply/job/<int:job_id>/', views.apply_for_job, name='apply_for_job_job'),
    path('apply/job/<int:job_id>/<str:next_page>/', views.apply_for_job, name='apply_for_job_job_redirect'),
    path('apply/needchef/<int:needchef_id>/', views.apply_for_job, name='apply_for_job_needchef'),
    path('apply/needchef/<int:needchef_id>/<str:next_page>/', views.apply_for_job, name='apply_for_job_needchef_redirect'),

    path("my-jobs/", views.my_jobs, name="my_jobs"),

    # User settings
    path("chef_settings/", views.chef_settings, name="chef_settings"),
    path("employer_settings/", views.employer_settings, name="employer_settings"),
    path("settings/upgrade-subscription/", views.upgrade_subscription, name="upgrade_subscription"),
    path("settings/change-password/", change_password_view.as_view(), name="change_password"),
    path("settings/reset-password/", reset_password_view.as_view(), name="reset_password"),
    path("settings/upgrade-verified/", views.upgrade_verified, name="upgrade_verified"),



    path("settings/verified/", views.upgrade_verified, name="upgrade_verified"),
    path("verified/", views.verified_handle_page, name="verified_handle_page"),
    path("verify/checkout/", views.verified_checkout, name="verified_checkout"),

    # Paystack
    path("paystack/init/", views.paystack_init, name="paystack_init"),
    path("paystack/callback/", views.paystack_callback, name="paystack_callback"),
    # Flutterwave
    path("flutter/init/", views.flutter_init, name="flutter_init"),
    path("flutter/callback/", views.flutter_callback, name="flutter_callback"),


    # Built-in password reset views
    path("reset-password/", auth_views.PasswordResetView.as_view(
        template_name="dashboard/password_reset.html",
        email_template_name="dashboard/password_reset_verify.html",
    ), name="password_reset"),

    path("reset-password/done/", auth_views.PasswordResetDoneView.as_view(
        template_name="dashboard/password_reset_done.html",
    ), name="password_reset_done"),

    path("reset/<uidb64>/<token>/", auth_views.PasswordResetConfirmView.as_view(
        template_name="dashboard/password_reset_confirm.html",
        success_url=reverse_lazy("password_reset_complete"),
    ), name="password_reset_confirm"),

    path("reset/complete/", auth_views.PasswordResetCompleteView.as_view(
        template_name="dashboard/password_reset_complete.html",
    ), name="password_reset_complete"),
]
