import json
import uuid
from datetime import *
from django.utils import timezone
from threading import Timer

from django.shortcuts import render
from django.contrib.auth import authenticate, login
from . import clients
from .models import Authorization
from django.contrib.auth.models import User
from django.core.exceptions import ObjectDoesNotExist

# Create your views here.
from django.http import HttpResponse

def signin(request):
    return render(request, "login.html")


def signin_failure(request):
    return render(request, "login.html", {"message": "<span class='error'>Error logging in</span>"})


def purge():
    auths = Authorization.objects.filter(expires__lt=timezone.now())

    for a in auths:
        for c in clients.clients:
            if a.id == c.auth_id:
                print(a)
                clients.clients.remove(c)

    auths.delete()


# STEP 1 - first login
def auth_first(request):
    username = request.POST.get('username')
    password = request.POST.get('password')

    # Get user
    user = authenticate(username=username, password=password)

    # Verify credentials
    if user is None:
        return signin_failure(request)

    # Create and store authorization and pass codes
    userObj = User.objects.get(username=username)

    a = Authorization(user=userObj, token1=uuid.uuid4(), password=password)
    a.save()

    # Start cleanup timer
    timer = Timer(30.0, purge)
    timer.start()  # after 30 seconds, "hello, world" will be printed

    #  Pass auth_id to client via template
    return render(request, "authenticating.html", { "auth_id": a.id })


# STEP 2 - authorization request
def authorize(request, token):
    try:
        authObj = Authorization.objects.get(token1=token)

        # Find corresponding client and allow access via websocket
        for c in clients.clients:
            if c.auth_id == authObj.id:

                #   Create 2nd token
                authObj.token1 = ''
                authObj.token2 = uuid.uuid4()
                authObj.save()

                c.send(text_data=json.dumps({'message': 'authorized', 'token': str(authObj.token2)}))
                return HttpResponse("THANK YOU", content_type='text/plain')

        print("authorize: client %s not found", authObj.id)

    except ObjectDoesNotExist as e:
        print(e)
        pass

    return HttpResponse("FORBIDDEN", content_type='text/plain')


# STEP 3 - second login
def auth_second(request):
    token = request.GET.get('token','unknown')

    # Check empty token
    if token == '':
        print("auth_second: empty token")
        return signin_failure(request)

    # Get login info from token2
    try:
        authObj = Authorization.objects.get(token2=token)
        userObj = User.objects.get(username=authObj.user)

    except ObjectDoesNotExist as e:
        print(e)
        return signin_failure(request)

    username = userObj.username
    password = authObj.password

    user = authenticate(username=username, password=password)

    if user is None:
        print("auth_second: authenticate failed %s:%s" , (username, password))
        return signin_failure(request)

    login(request, user)

    # Delete access tokens
    authObj.delete()

    return render(request, "home.html")


# Default to login
def index(request):
    return signin(request)
