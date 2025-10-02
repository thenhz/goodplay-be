from typing import Optional
from flask import current_app, render_template_string
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
import os

class EmailService:
    """Service for sending emails"""

    def __init__(self):
        self.smtp_server = os.getenv('SMTP_SERVER', 'smtp.gmail.com')
        self.smtp_port = int(os.getenv('SMTP_PORT', '587'))
        self.smtp_username = os.getenv('SMTP_USERNAME', '')
        self.smtp_password = os.getenv('SMTP_PASSWORD', '')
        self.from_email = os.getenv('FROM_EMAIL', 'noreply@goodplay.com')
        self.from_name = os.getenv('FROM_NAME', 'GoodPlay')
        self.frontend_url = os.getenv('FRONTEND_URL', 'http://localhost:3000')

    def send_verification_email(self, to_email: str, verification_token: str, first_name: Optional[str] = None) -> bool:
        """Send email verification email to user"""
        try:
            verification_url = f"{self.frontend_url}/verify-email?token={verification_token}"

            subject = "Verify your GoodPlay account"

            # HTML email template
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Welcome to GoodPlay!</h1>
                    </div>
                    <div class="content">
                        <p>Hello{f' {first_name}' if first_name else ''},</p>
                        <p>Thank you for registering with GoodPlay. Please verify your email address by clicking the button below:</p>
                        <p style="text-align: center;">
                            <a href="{verification_url}" class="button">Verify Email Address</a>
                        </p>
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #666;">{verification_url}</p>
                        <p>This link will expire in 24 hours.</p>
                        <p>If you didn't create an account with GoodPlay, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 GoodPlay. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            # Plain text version
            text_body = f"""
            Hello{f' {first_name}' if first_name else ''},

            Thank you for registering with GoodPlay. Please verify your email address by clicking the link below:

            {verification_url}

            This link will expire in 24 hours.

            If you didn't create an account with GoodPlay, please ignore this email.

            © 2025 GoodPlay. All rights reserved.
            """

            return self._send_email(to_email, subject, text_body, html_body)

        except Exception as e:
            current_app.logger.error(f"Error sending verification email: {str(e)}")
            return False

    def send_password_reset_email(self, to_email: str, reset_token: str, first_name: Optional[str] = None) -> bool:
        """Send password reset email to user"""
        try:
            reset_url = f"{self.frontend_url}/reset-password?token={reset_token}"

            subject = "Reset your GoodPlay password"

            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; color: #333; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background-color: #4CAF50; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background-color: #f9f9f9; }}
                    .button {{ display: inline-block; padding: 12px 24px; background-color: #4CAF50; color: white; text-decoration: none; border-radius: 4px; margin: 20px 0; }}
                    .footer {{ padding: 20px; text-align: center; font-size: 12px; color: #666; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>Password Reset Request</h1>
                    </div>
                    <div class="content">
                        <p>Hello{f' {first_name}' if first_name else ''},</p>
                        <p>We received a request to reset your GoodPlay password. Click the button below to reset it:</p>
                        <p style="text-align: center;">
                            <a href="{reset_url}" class="button">Reset Password</a>
                        </p>
                        <p>Or copy and paste this link in your browser:</p>
                        <p style="word-break: break-all; color: #666;">{reset_url}</p>
                        <p>This link will expire in 1 hour.</p>
                        <p>If you didn't request a password reset, please ignore this email.</p>
                    </div>
                    <div class="footer">
                        <p>&copy; 2025 GoodPlay. All rights reserved.</p>
                    </div>
                </div>
            </body>
            </html>
            """

            text_body = f"""
            Hello{f' {first_name}' if first_name else ''},

            We received a request to reset your GoodPlay password. Click the link below to reset it:

            {reset_url}

            This link will expire in 1 hour.

            If you didn't request a password reset, please ignore this email.

            © 2025 GoodPlay. All rights reserved.
            """

            return self._send_email(to_email, subject, text_body, html_body)

        except Exception as e:
            current_app.logger.error(f"Error sending password reset email: {str(e)}")
            return False

    def _send_email(self, to_email: str, subject: str, text_body: str, html_body: str) -> bool:
        """Internal method to send email via SMTP"""
        try:
            # Create message
            message = MIMEMultipart('alternative')
            message['Subject'] = subject
            message['From'] = f"{self.from_name} <{self.from_email}>"
            message['To'] = to_email

            # Attach text and HTML parts
            text_part = MIMEText(text_body, 'plain')
            html_part = MIMEText(html_body, 'html')

            message.attach(text_part)
            message.attach(html_part)

            # Check if SMTP is configured
            if not self.smtp_username or not self.smtp_password:
                current_app.logger.warning(f"SMTP not configured. Email would be sent to {to_email}")
                # In development, just log the email
                current_app.logger.info(f"Email subject: {subject}")
                current_app.logger.info(f"Email body: {text_body}")
                return True

            # Send email via SMTP
            with smtplib.SMTP(self.smtp_server, self.smtp_port) as server:
                server.starttls()
                server.login(self.smtp_username, self.smtp_password)
                server.send_message(message)

            current_app.logger.info(f"Email sent successfully to {to_email}")
            return True

        except Exception as e:
            current_app.logger.error(f"Error sending email: {str(e)}")
            return False
