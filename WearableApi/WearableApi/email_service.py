from sendgrid import SendGridAPIClient
from sendgrid.helpers.mail import Mail, Email, To
from django.conf import settings
import logging

logger = logging.getLogger(__name__)


class EmailService:
    def __init__(self):
        self.client = SendGridAPIClient(settings.SENDGRID_API_KEY)
        self.from_email = settings.DEFAULT_FROM_EMAIL
    
    def send_password_reset(self, user_email, reset_link):
        """Send password reset email"""
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(user_email),
            subject='Reset Your Password',
            html_content=f'''
            <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h2>Password Reset Request</h2>
                    <p>Click the link below to reset your password:</p>
                    <a href="{reset_link}" 
                       style="background: #4CAF50; color: white; padding: 10px 20px; 
                              text-decoration: none; border-radius: 5px;">
                        Reset Password
                    </a>
                    <p>This link expires in 1 hour.</p>
                </body>
            </html>
            '''
        )
        
        try:
            response = self.client.send(message)
            logger.info(f"Password reset sent to {user_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False
    
    def send_craving_alert(self, user_email, probability):
        """Send high craving risk alert"""
        risk_percent = probability * 100
        
        message = Mail(
            from_email=Email(self.from_email),
            to_emails=To(user_email),
            subject=f'⚠️ High Craving Risk Alert ({risk_percent:.0f}%)',
            html_content=f'''
            <html>
                <body style="font-family: Arial; padding: 20px;">
                    <h2 style="color: #d32f2f;">⚠️ Craving Alert</h2>
                    <p>Your craving risk is <strong>{risk_percent:.1f}%</strong></p>
                    
                    <div style="background: #fff3cd; padding: 15px; border-radius: 5px;">
                        <h3>Recommended Actions:</h3>
                        <ul>
                            <li>Take 10 deep breaths</li>
                            <li>Go for a 5-minute walk</li>
                            <li>Drink a glass of water</li>
                            <li>Call your support person</li>
                        </ul>
                    </div>
                    
                    <p style="color: #4CAF50; font-size: 18px;">
                        You've got this! 💪
                    </p>
                </body>
            </html>
            '''
        )
        
        try:
            response = self.client.send(message)
            logger.info(f"Craving alert sent to {user_email}")
            return response.status_code == 202
        except Exception as e:
            logger.error(f"Email failed: {e}")
            return False