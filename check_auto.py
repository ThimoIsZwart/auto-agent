import os
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

print("Seat Leon Agent gestart")

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

URL = "https://www.gaspedaal.nl/seat/leon/benzine?bmin=2016&pmax=12500&kmax=150000&trns=HANDMATIG&klr=ZWART&srt=df-a"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers, timeout=20)

print("Status:", response.status_code)

soup = BeautifulSoup(response.text, "html.parser")

gevonden = set()

for link in soup.find_all("a", href=True):
    href = link["href"]

    if "/seat/" in href.lower() or "/auto/" in href.lower():
        if href.startswith("/"):
            href = "https://www.gaspedaal.nl" + href

        gevonden.add(href)

if os.path.exists("seen_ads.txt"):
    with open("seen_ads.txt", "r", encoding="utf-8") as f:
        gezien = set(line.strip() for line in f)
else:
    gezien = set()

nieuwe = gevonden - gezien

print("Gevonden:", len(gevonden))
print("Nieuw:", len(nieuwe))

if nieuwe:

    inhoud = "Nieuwe Seat Leon advertenties:\n\n"

    for advertentie in sorted(nieuwe):
        inhoud += advertentie + "\n\n"

    msg = MIMEText(inhoud, "plain", "utf-8")

    msg["Subject"] = f"{len(nieuwe)} nieuwe Seat Leon advertentie(s)"
    msg["From"] = EMAIL
    msg["To"] = EMAIL

    server = smtplib.SMTP("smtp.gmail.com", 587)
    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

    with open("seen_ads.txt", "a", encoding="utf-8") as f:
        for advertentie in sorted(nieuwe):
            f.write(advertentie + "\n")

    print("Mail verzonden")

else:
    print("Geen nieuwe advertenties")
