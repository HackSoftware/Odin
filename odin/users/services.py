from typing import Dict

from django.core.exceptions import ValidationError

from .models import BaseUser, Profile


def get_gh_email_address(request):
    """
    COMMENT:
    This is definetely not a service. Looks like a util for the allauth view.
    """
    socialaccount = request.session.get('socialaccount_sociallogin', {})
    email_address = socialaccount.get('email_addresses', None)
    if email_address is not None:
        return email_address[0].get('email', '')


def update_user_profile(*,
                        user: BaseUser,
                        data: Dict[str, str]) -> Profile:
    pass


def create_user(*,
                email: str,
                password: str=None,
                profile_data: Dict[str, str]=None) -> BaseUser:
    if BaseUser.objects.filter(email=email).exists():
        raise ValidationError('User already exists.')

    user = BaseUser.objects.create(email=email, password=password)

    update_user_profile(user=user, data=profile_data)

    return user
