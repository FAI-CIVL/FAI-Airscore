from flask import render_template, url_for
from flask_mail import Message

from airscore.app import create_app
from airscore.extensions import mail

app = create_app()
app.app_context().push()


def send_email(subject, sender, recipients, text_body, html_body):
    msg = Message(subject, sender=sender, recipients=recipients)
    msg.body = text_body
    msg.html = html_body
    mail.send(msg)


def send_password_reset_email(user):
    with app.app_context(), app.test_request_context():

        token = user.get_reset_password_token()
        send_email(
            '[Airscore] Reset Your Password',
            sender=app.config['ADMINS'],
            recipients=[user.email],
            text_body=render_template('email/reset_password.txt', user=user, token=token),
            html_body=render_template('email/reset_password.html', user=user, token=token),
        )
