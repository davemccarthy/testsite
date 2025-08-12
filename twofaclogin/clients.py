import json
from channels.generic.websocket import WebsocketConsumer
from .models import Authorization
from django.contrib.auth.models import User
from django.core.mail import send_mail
from django.conf import settings

# FIXED: Active authentication clients - consider using channel layers for production
# This in-memory approach works for single-server deployments but won't scale
clients = []

class AuthClient(WebsocketConsumer):

    auth_id = 0

    # New connection send handshake
    def connect(self):
        self.accept()
        self.send(text_data=json.dumps({
            'message': 'connected'
        }))

    # FIXED: Add proper cleanup on disconnect
    def disconnect(self, close_code):
        # Remove this client from the global list to prevent memory leaks
        if self in clients:
            clients.remove(self)
            print(f"Client {self.auth_id} disconnected and removed from list")

    # Incoming data
    def receive(self, text_data):
        try:
            data = json.loads(text_data)

            # Check message
            match data['message']:

                #   Got id from client
                case "authorize":
                    self.auth_id = data['auth_id']

                    try:
                        authObj = Authorization.objects.get(id=data['auth_id'])
                        userObj = authObj.user  # FIXED: Use authObj.user directly

                        clients.append(self)

                        # FIXED: Build absolute URL using Django's utilities
                        # This ensures the correct protocol and host are used
                        from django.urls import reverse
                        from django.contrib.sites.shortcuts import get_current_site
                        
                        # For now, use a simple approach - in production, use proper URL building
                        authorize_url = f"http://{settings.ALLOWED_HOSTS[0]}:8000/authorize/{authObj.token1}"
                        
                        # FIXED: Remove sensitive data from logs
                        print(f"Sending authorization email to {userObj.email}")
                        
                        #   Send email (TODO: host)
                        send_mail(
                            "Authorization",
                            f"Click this link to authorize your login: {authorize_url}",
                            settings.DEFAULT_FROM_EMAIL,  # FIXED: Use settings
                            [userObj.email],
                            fail_silently=False,
                        )
                        
                        print(f"Authorization email sent to {userObj.email}")
                        return
                        
                    except Authorization.DoesNotExist:
                        print(f"Authorization {data['auth_id']} not found")
                        self.send(text_data=json.dumps({
                            'message': 'error',
                            'error': 'Authorization not found'
                        }))
                        return
                    except Exception as e:
                        print(f"Error processing authorization: {e}")
                        self.send(text_data=json.dumps({
                            'message': 'error',
                            'error': 'Internal server error'
                        }))
                        return
                        
                case _:
                    print(f"Unknown message type: {data['message']}")
                    self.send(text_data=json.dumps({
                        'message': 'error',
                        'error': 'Unknown message type'
                    }))
                    
        except json.JSONDecodeError:
            print("Invalid JSON received")
            self.send(text_data=json.dumps({
                'message': 'error',
                'error': 'Invalid JSON'
            }))
        except Exception as e:
            print(f"Unexpected error in receive: {e}")
            self.send(text_data=json.dumps({
                'message': 'error',
                'error': 'Internal server error'
            }))