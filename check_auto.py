import os
import smtplib

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

server = smtplib.SMTP("smtp.gmail.com", 587)
server.starttls()

server.login(EMAIL, PASSWORD)

onderwerp = "Auto Agent Test"
bericht = """
Dit is een testmail van je GitHub Auto Agent.

Als je dit ontvangt werkt alles goed.
"""

server.sendmail(
    EMAIL,
    EMAIL,
    f"Subject: {onderwerp}\n\n{bericht}"
)

server.quit()

print("Mail verzonden")
