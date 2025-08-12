import json
import uuid
from datetime import *
from django.utils import timezone
# REMOVED: threading.Timer - not safe for web workers, will use DB-based expiry checks instead

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from . import clients
from .models import Authorization
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist
from django.http import HttpResponse, HttpResponseForbidden
from django.urls import reverse

# Create your views here.

def signin(request):
    return render(request, "login.html")


def signin_failure(request):
    return render(request, "login.html", {"message": "<span class='error'>Error logging in</span>"})


# REMOVED: purge() function - threading.Timer approach is not safe for web workers
# Instead, we'll check expiry in each view and use a management command for cleanup
def cleanup_expired_auths():
    """Clean up expired authorizations - call this periodically or in views"""
    expired_count = Authorization.objects.filter(expires__lt=timezone.now()).delete()[0]
    if expired_count > 0:
        print(f"Cleaned up {expired_count} expired authorizations")


# STEP 1 - first login
def auth_first(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

    # Get user
    user = authenticate(username=username, password=password)

    # Verify credentials
    if user is None:
        return signin_failure(request)

    # Clean up any existing expired authorizations
    cleanup_expired_auths()

    # Create and store authorization with new token1
    # REMOVED: password storage - security vulnerability
    a = Authorization(user=user)
    a.save()

    # Pass auth_id to client via template
    return render(request, "authenticating.html", { "auth_id": a.id })


# STEP 2 - authorization request
def authorize(request, token):
    try:
        # FIXED: Add expiry check to prevent use of expired tokens
        authObj = Authorization.objects.get(
            token1=token, 
            expires__gt=timezone.now()
        )

        # Find corresponding client and allow access via websocket
        for c in clients.clients:
            if c.auth_id == authObj.id:
                # FIXED: Generate new token2 instead of overwriting token1
                authObj.token2 = uuid.uuid4()
                # FIXED: Clear token1 to prevent reuse
                authObj.token1 = None
                authObj.save()

                c.send(text_data=json.dumps({
                    'message': 'authorized', 
                    'token': str(authObj.token2)
                }))
                return HttpResponse("THANK YOU", content_type='text/plain')

        print(f"authorize: client {authObj.id} not found")
        return HttpResponseForbidden("Client not found")

    except ObjectDoesNotExist as e:
        print(f"authorize: token not found or expired: {e}")
        return HttpResponseForbidden("Invalid or expired token")


# STEP 3 - second login
def auth_second(request):
    token = request.GET.get('token', 'unknown')

    # Check empty token
    if token == '':
        print("auth_second: empty token")
        return signin_failure(request)

    # FIXED: Add expiry check and use token2
    try:
        authObj = Authorization.objects.get(
            token2=token, 
            expires__gt=timezone.now()
        )
        # FIXED: Use authObj.user directly instead of re-fetching
        user = authObj.user

    except ObjectDoesNotExist as e:
        print(f"auth_second: token not found or expired: {e}")
        return signin_failure(request)

    # FIXED: No need to re-authenticate - we trust the Authorization.user relationship
    # The user already authenticated in auth_first, and we validate token2 + expiry
    login(request, user)

    # Delete access tokens
    authObj.delete()

    return render(request, "home.html")


# Default to login
def index(request):
    return signin(request)
