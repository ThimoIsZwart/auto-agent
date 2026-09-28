import os
import smtplib
from email.mime.text import MIMEText

print("test 17:40")

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

msg = MIMEText(
    "Dit is een testmail van je GitHub Auto Agent.\n\nAls je dit ontvangt werkt alles goed.",
    "plain",
    "utf-8"
)

msg["Subject"] = "Auto Agent Test"
msg["From"] = EMAIL
msg["To"] = EMAIL

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()

server.login(EMAIL, PASSWORD)
server.send_message(msg)

server.quit()

print("Mail verzonden")
