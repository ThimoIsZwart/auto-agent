import os
import re
import requests
import smtplib
from bs4 import BeautifulSoup
from email.mime.text import MIMEText

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

SEARCH_URL = "https://www.autoscout24.nl/lst/seat/leon/ft_benzine/tr_handgeschakeld/bc_zwart?priceto=12500&fregfrom=2016&cy=NL&damaged_listing=exclude&desc=0&kmto=150000&powertype=kw&sort=standard&ustate=N%2CU&atype=C&mcat=ma64mo15869"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

response = requests.get(SEARCH_URL, headers=HEADERS)

matches = re.findall(r'/aanbod/[^"]+', response.text)

gevonden = set()

for link in matches:
    if "seat-leon" not in link.lower():
        continue

    gevonden.add("https://www.autoscout24.nl" + link)

if os.path.exists("seen_ads.txt"):
    with open("seen_ads.txt", "r", encoding="utf-8") as f:
        gezien = set(line.strip() for line in f)
else:
    gezien = set()

nieuwe = gevonden - gezien

print("Nieuw:", len(nieuwe))

if nieuwe:

    kaarten = ""

    for advertentie in sorted(nieuwe):

        titel = "Seat Leon"
        prijs = "Onbekend"
        kmstand = "Onbekend"
        bouwjaar = "Onbekend"
        brandstof = "Onbekend"
        transmissie = "Onbekend"

        try:

            pagina = requests.get(
                advertentie,
                headers=HEADERS,
                timeout=20
            )

            soup = BeautifulSoup(
                pagina.text,
                "html.parser"
            )

            if soup.title:
                titel = soup.title.text.split("|")[0].strip()

            tekst = soup.get_text(
                " ",
                strip=True
            )

            prijs_match = re.search(
                r'€\s?[0-9\.\,]+',
                tekst
            )

            if prijs_match:
                prijs = prijs_match.group(0)

            km_match = re.search(
                r'([0-9\.]{2,10})\s*km',
                tekst,
                re.IGNORECASE
            )

            if km_match:
                kmstand = km_match.group(1) + " km"

            bouwjaar_match = re.search(
                r'\b(20[0-2][0-9]|19[9][0-9])\b',
                tekst
            )

            if bouwjaar_match:
                bouwjaar = bouwjaar_match.group(1)

            if "Benzine" in tekst:
                brandstof = "Benzine"

            if "Handgeschakeld" in tekst:
                transmissie = "Handgeschakeld"

        except Exception as e:
            print("Fout:", e)

        kaarten += f"""
        <div style="
            border:1px solid #dcdcdc;
            border-radius:12px;
            padding:16px;
            margin-bottom:20px;
            background:#fafafa;
        ">

            <h2 style="margin:0;color:#0f62fe;">
                🚗 {titel}
            </h2>

            <p>
                💰 <b>{prijs}</b><br>
                📅 <b>{bouwjaar}</b><br>
                🛣️ <b>{kmstand}</b><br>
                ⛽ <b>{brandstof}</b><br>
                ⚙️ <b>{transmissie}</b>
            </p>

            <p>
                {advertentie}
                    Bekijk advertentie
                </a>
            </p>

        </div>
        """

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif;">

        <h1 style="color:#0f62fe;">
            🚗 Nieuwe Seat Leon advertenties
        </h1>

        <p>
            Er zijn vandaag
            <strong>{len(nieuwe)}</strong>
            nieuwe advertenties gevonden.
        </p>

        <p>
            Criteria:
        </p>

        <ul>
            <li>Seat Leon</li>
            <li>Benzine</li>
            <li>Handgeschakeld</li>
            <li>Zwart</li>
            <li>Bouwjaar vanaf 2016</li>
            <li>Tot €12.500</li>
            <li>Max 150.000 km</li>
        </ul>

        {kaarten}

        <hr>

        <small>
            Automatisch verstuurd door jouw GitHub Auto Agent.
        </small>

    </body>
    </html>
    """

    msg = MIMEText(
        html,
        "html",
        "utf-8"
    )

    msg["Subject"] = (
        f"🚗 {len(nieuwe)} nieuwe Seat Leon advertentie(s)"
    )

    msg["From"] = EMAIL
    msg["To"] = EMAIL

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()
    server.login(EMAIL, PASSWORD)
    server.send_message(msg)
    server.quit()

    with open(
        "seen_ads.txt",
        "a",
        encoding="utf-8"
    ) as f:

        for advertentie in sorted(nieuwe):
            f.write(advertentie + "\n")

    print("Mail verzonden")

else:
    print("Geen nieuwe advertenties")
