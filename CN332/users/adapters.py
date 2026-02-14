<<<<<<< HEAD
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
=======
from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoNewSocialSignupAdapter(DefaultSocialAccountAdapter):
>>>>>>> f43e35878f6a4da553ea6de92c037bf736c811ff
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

<<<<<<< HEAD
        email = sociallogin.user.email

        if not email:
            messages.error(
                request,
                "ไม่สามารถเข้าสู่ระบบได้ (ไม่พบอีเมลจากผู้ให้บริการ)"
            )
            raise ImmediateHttpResponse(redirect("login"))

        if not User.objects.filter(email__iexact=email).exists():
            messages.error(
                request,
                "ไม่พบอีเมลนี้ในระบบ กรุณาติดต่อผู้ดูแลระบบ"
            )
            raise ImmediateHttpResponse(redirect("login"))
=======
        if request.user.is_authenticated:
            return

        messages.error(request, 'This social account is not linked. Please link it from Settings first.')
        raise ImmediateHttpResponse(redirect('login'))

    def is_open_for_signup(self, request, sociallogin):
        return False

    def get_connect_redirect_url(self, request, socialaccount):
        return '/settings/'

    def get_disconnect_redirect_url(self, request, socialaccount):
        return '/settings/'
>>>>>>> f43e35878f6a4da553ea6de92c037bf736c811ff
