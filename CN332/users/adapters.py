from allauth.socialaccount.adapter import DefaultSocialAccountAdapter
from allauth.exceptions import ImmediateHttpResponse
from django.contrib import messages
from django.shortcuts import redirect
from django.contrib.auth import get_user_model

User = get_user_model()


class CustomSocialAccountAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

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
