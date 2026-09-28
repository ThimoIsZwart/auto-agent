import os
import re
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

URL = "https://www.autoscout24.nl/lst/seat/leon/ft_benzine/tr_handgeschakeld/bc_zwart?priceto=12500&fregfrom=2016&cy=NL&damaged_listing=exclude&desc=0&kmto=150000&powertype=kw&sort=standard&ustate=N%2CU&atype=C&mcat=ma64mo15869"

headers = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(URL, headers=headers)

print("Status:", response.status_code)

matches = re.findall(r'/aanbod/[^"]+', response.text)

gevonden = set()

for link in matches:

    if "seat-leon" not in link.lower():
        continue

    volledige_link = "https://www.autoscout24.nl" + link
    gevonden.add(volledige_link)

print("Leon advertenties:", len(gevonden))

if os.path.exists("seen_ads.txt"):
    with open("seen_ads.txt", "r", encoding="utf-8") as f:
        gezien = set(line.strip() for line in f)
else:
    gezien = set()

nieuwe = gevonden - gezien

print("Nieuw:", len(nieuwe))

if nieuwe:

    inhoud = """
🚗 SEAT LEON AGENT

Er zijn nieuwe advertenties gevonden die voldoen aan jouw wensen:

✅ Seat Leon
✅ Benzine
✅ Handgeschakeld
✅ Zwart
✅ Vanaf 2016
✅ Max €12.500
✅ Max 150.000 km

"""

    for nummer, advertentie in enumerate(sorted(nieuwe), start=1):

        titel = advertentie.split("/aanbod/")[1]
        titel = titel.split("-cat_")[0]
        titel = titel.replace("-", " ").title()

        inhoud += f"""

══════════════════════════════════════

🚗 Advertentie #{nummer}

📝 {titel}

🔗 Link:
{advertentie}

"""

    inhoud += """

══════════════════════════════════════

Dit overzicht is automatisch gegenereerd door jouw GitHub Auto Agent.

Veel succes met de zoektocht! 🚗
"""

    msg = MIMEText(inhoud, "plain", "utf-8")

    msg["Subject"] = f"🚗 {len(nieuwe)} nieuwe Seat Leon advertentie(s)"
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
