import smtplib
import logging
from email.mime.text import MIMEText

class Postman:

    def __init__(self, sender_email, sender_pwd, receiver_email) :
        self.sender = sender_email
        self.receivers = [receiver_email]
        self.title = ''
        self.contents = ''
        self.pwd = sender_pwd

    def _send_email(self) :
        # Send email to all receivers
        for receiver in self.receivers:
            msg = MIMEText(self.contents)
            msg['Subject'] = self.title
            msg['From'] = self.sender
            msg['To'] = receiver
            logging.debug(msg)

            smtp_gmail = smtplib.SMTP_SSL('smtp.gmail.com', 465)
            smtp_gmail.login(self.sender, self.pwd)
            smtp_gmail.sendmail(self.sender, receiver, msg.as_string())
            smtp_gmail.quit()

    def send(self, title, content) :
        self.title = title
        self.contents = content
        self._send_email()
