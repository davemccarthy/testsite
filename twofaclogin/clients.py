import json
from channels.generic.websocket import WebsocketConsumer
from .models import Authorization
from django.contrib.auth.models import User
from django.core.mail import send_mail

# Active authentication clients
clients = []

class AuthClient(WebsocketConsumer):

    auth_id = 0

    # New connection send handshake
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'message': 'connected'
        }))

    # Disconnected
    def disconnect(self, close_code):
        pass

    # Incoming data
    def receive(self, text_data):

        data = json.loads(text_data)

        # Check message
        match data['message']:

            #   Got id from client
            case "authorize":

                self.auth_id = data['auth_id']

                authObj = Authorization.objects.get(id = data['auth_id'])
                userObj = User.objects.get(username = authObj.user)

                clients.append(self)

                #   Send email (TODO: host)
                send_mail(
                    "Authorization",
                    "http://192.168.1.6:8000/authorize/%s" % authObj.token1,
                    "dave@klynt.com",
                    [userObj.email],
                    fail_silently=False,
                )

                print(authObj.token1)
                print(authObj.user)
                print(userObj.email)
                return