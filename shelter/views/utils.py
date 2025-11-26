from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages


def is_admin_user(user):
    """Check if user is staff/admin"""
    return user.is_authenticated and (user.is_staff or user.is_superuser)