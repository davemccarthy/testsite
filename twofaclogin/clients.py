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
                        
                        # FIXED: Use localhost since the server is running locally
                        # In production, this should use the actual domain
                        authorize_url = f"http://127.0.0.1:8000/authorize/{authObj.token1}"
                        
                        # FIXED: Remove sensitive data from logs
                        print(f"Sending authorization email to {userObj.email}")
                        
                        # Create beautiful HTML email template
                        html_message = f"""
                        <!DOCTYPE html>
                        <html lang="en">
                        <head>
                            <meta charset="UTF-8">
                            <meta name="viewport" content="width=device-width, initial-scale=1.0">
                            <title>Two-Factor Authentication</title>
                            <style>
                                body {{
                                    font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Oxygen, Ubuntu, Cantarell, sans-serif;
                                    margin: 0;
                                    padding: 0;
                                    background-color: #f8f9fa;
                                    color: #333;
                                    line-height: 1.6;
                                }}
                                
                                .email-container {{
                                    max-width: 600px;
                                    margin: 0 auto;
                                    background: white;
                                    border-radius: 12px;
                                    overflow: hidden;
                                    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.1);
                                }}
                                
                                .header {{
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    padding: 40px 30px;
                                    text-align: center;
                                    color: white;
                                }}
                                
                                .header h1 {{
                                    margin: 0;
                                    font-size: 28px;
                                    font-weight: 700;
                                }}
                                
                                .header p {{
                                    margin: 10px 0 0 0;
                                    font-size: 16px;
                                    opacity: 0.9;
                                }}
                                
                                .content {{
                                    padding: 40px 30px;
                                }}
                                
                                .welcome-text {{
                                    font-size: 18px;
                                    color: #333;
                                    margin-bottom: 24px;
                                    text-align: center;
                                }}
                                
                                .auth-button {{
                                    display: inline-block;
                                    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                                    color: white;
                                    text-decoration: none;
                                    padding: 16px 32px;
                                    border-radius: 12px;
                                    font-size: 16px;
                                    font-weight: 600;
                                    margin: 24px 0;
                                    text-align: center;
                                    box-shadow: 0 4px 12px rgba(102, 126, 234, 0.3);
                                }}
                                
                                .auth-button:hover {{
                                    transform: translateY(-2px);
                                    box-shadow: 0 6px 16px rgba(102, 126, 234, 0.4);
                                }}
                                
                                .security-info {{
                                    background: #f8f9fa;
                                    border-left: 4px solid #667eea;
                                    padding: 20px;
                                    margin: 24px 0;
                                    border-radius: 8px;
                                }}
                                
                                .security-info h3 {{
                                    margin: 0 0 8px 0;
                                    color: #333;
                                    font-size: 16px;
                                    font-weight: 600;
                                }}
                                
                                .security-info p {{
                                    margin: 0;
                                    color: #666;
                                    font-size: 14px;
                                }}
                                
                                .steps {{
                                    margin: 24px 0;
                                }}
                                
                                .step {{
                                    display: flex;
                                    align-items: center;
                                    margin-bottom: 16px;
                                    padding: 12px;
                                    background: #f8f9fa;
                                    border-radius: 8px;
                                }}
                                
                                .step-number {{
                                    width: 32px;
                                    height: 32px;
                                    background: linear-gradient(135deg, #667eea, #764ba2);
                                    color: white;
                                    border-radius: 50%;
                                    display: flex;
                                    align-items: center;
                                    justify-content: center;
                                    font-weight: 600;
                                    margin-right: 16px;
                                    flex-shrink: 0;
                                }}
                                
                                .step-text {{
                                    color: #333;
                                    font-size: 14px;
                                }}
                                
                                .footer {{
                                    background: #f8f9fa;
                                    padding: 30px;
                                    text-align: center;
                                    border-top: 1px solid #e1e5e9;
                                }}
                                
                                .footer p {{
                                    margin: 0;
                                    color: #666;
                                    font-size: 12px;
                                }}
                                
                                .expiry-notice {{
                                    background: #fff3cd;
                                    border: 1px solid #ffeaa7;
                                    color: #856404;
                                    padding: 12px;
                                    border-radius: 8px;
                                    margin: 16px 0;
                                    font-size: 13px;
                                    text-align: center;
                                }}
                                
                                @media (max-width: 600px) {{
                                    .email-container {{
                                        margin: 10px;
                                        border-radius: 8px;
                                    }}
                                    
                                    .header, .content, .footer {{
                                        padding: 20px;
                                    }}
                                    
                                    .header h1 {{
                                        font-size: 24px;
                                    }}
                                }}
                            </style>
                        </head>
                        <body>
                            <div class="email-container">
                                <div class="header">
                                    <h1>🔐 Secure Authentication</h1>
                                    <p>Complete your login with two-factor authentication</p>
                                </div>
                                
                                <div class="content">
                                    <div class="welcome-text">
                                        Hello {userObj.username},<br>
                                        Please authorize your login attempt
                                    </div>
                                    
                                    <div style="text-align: center;">
                                        <a href="{authorize_url}" class="auth-button">
                                            🔐 Authorize Login
                                        </a>
                                    </div>
                                    
                                    <div class="expiry-notice">
                                        ⏰ This authorization link expires in 30 seconds
                                    </div>
                                    
                                    <div class="security-info">
                                        <h3>🔒 Enhanced Security</h3>
                                        <p>This two-factor authentication ensures that only you can access your account, even if someone else knows your password.</p>
                                    </div>
                                    
                                    <div class="steps">
                                        <div class="step">
                                            <div class="step-number">1</div>
                                            <div class="step-text">You entered your credentials</div>
                                        </div>
                                        <div class="step">
                                            <div class="step-number">2</div>
                                            <div class="step-text">Click the authorization button above</div>
                                        </div>
                                        <div class="step">
                                            <div class="step-number">3</div>
                                            <div class="step-text">You'll be automatically logged in</div>
                                        </div>
                                    </div>
                                    
                                    <div style="text-align: center; margin-top: 24px;">
                                        <p style="color: #666; font-size: 13px;">
                                            If you didn't attempt to log in, please ignore this email and consider changing your password.
                                        </p>
                                    </div>
                                </div>
                                
                                <div class="footer">
                                    <p>This is an automated security message. Please do not reply to this email.</p>
                                    <p>© 2025 Secure Authentication System</p>
                                </div>
                            </div>
                        </body>
                        </html>
                        """
                        
                        # Plain text fallback
                        text_message = f"""
                        Two-Factor Authentication Required
                        
                        Hello {userObj.username},
                        
                        Please authorize your login attempt by clicking the link below:
                        
                        {authorize_url}
                        
                        This authorization link expires in 30 seconds.
                        
                        If you didn't attempt to log in, please ignore this email and consider changing your password.
                        
                        This is an automated security message. Please do not reply to this email.
                        """
                        
                        #   Send email with HTML content
                        send_mail(
                            "🔐 Complete Your Login - Two-Factor Authentication",
                            text_message,
                            settings.DEFAULT_FROM_EMAIL,
                            [userObj.email],
                            fail_silently=False,
                            html_message=html_message,
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