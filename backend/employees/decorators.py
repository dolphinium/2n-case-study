from django.contrib.auth.decorators import user_passes_test

def personnel_required(function=None, redirect_field_name='next', login_url='personnel_login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and not u.is_authorized,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator

def authorized_user_required(function=None, redirect_field_name='next', login_url='authorized_login'):
    actual_decorator = user_passes_test(
        lambda u: u.is_authenticated and u.is_authorized,
        login_url=login_url,
        redirect_field_name=redirect_field_name
    )
    if function:
        return actual_decorator(function)
    return actual_decorator