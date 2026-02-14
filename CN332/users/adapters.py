from django.contrib import messages
from django.contrib.auth import get_user_model
from django.shortcuts import redirect
from allauth.exceptions import ImmediateHttpResponse
from allauth.socialaccount.adapter import DefaultSocialAccountAdapter


class NoNewSocialSignupAdapter(DefaultSocialAccountAdapter):
    def pre_social_login(self, request, sociallogin):
        if sociallogin.is_existing:
            return

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
