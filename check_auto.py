import os
import re
import requests
import smtplib

from bs4 import BeautifulSoup
from email.mime.text import MIMEText

EMAIL = os.environ["EMAIL_USER"]
PASSWORD = os.environ["EMAIL_PASSWORD"]

MAX_PRIJS = 12500
MAX_KM = 150000
MIN_BOUWJAAR = 2016

SEARCH_URL = "https://www.autoscout24.nl/lst/seat/leon/ft_benzine/tr_handgeschakeld/bc_zwart?priceto=12500&fregfrom=2016&cy=NL&damaged_listing=exclude&desc=0&kmto=150000&powertype=kw&sort=standard&ustate=N%2CU&atype=C&mcat=ma64mo15869"

HEADERS = {
    "User-Agent": "Mozilla/5.0"
}

print("Seat Leon Agent gestart")

response = requests.get(
    SEARCH_URL,
    headers=HEADERS,
    timeout=30
)

print("Status:", response.status_code)

matches = re.findall(
    r'/aanbod/[^"]+',
    response.text
)

gevonden = set()

for link in matches:

    lower = link.lower()

    if "seat-leon" not in lower:
        continue

    gevonden.add(
        "https://www.autoscout24.nl" + link
    )

print("Leon advertenties:", len(gevonden))

if os.path.exists("seen_ads.txt"):
    with open(
        "seen_ads.txt",
        "r",
        encoding="utf-8"
    ) as f:

        gezien = set(
            x.strip()
            for x in f
            if x.strip()
        )
else:
    gezien = set()

nieuwe_links = gevonden - gezien

print("Nieuw:", len(nieuwe_links))

geldige_advertenties = []

for advertentie_url in sorted(nieuwe_links):

    try:

        pagina = requests.get(
            advertentie_url,
            headers=HEADERS,
            timeout=30
        )
        print("=== ADVERTENTIE HTML ===")
        print(pagina.text[:15000])
        break

        soup = BeautifulSoup(
            pagina.text,
            "html.parser"
        )

        titel = "Seat Leon"

        if soup.title:
            titel = (
                soup.title.text
                .split("|")[0]
                .strip()
            )

        tekst = soup.get_text(
            " ",
            strip=True
        )

        prijs = None
        kmstand = None
        bouwjaar = None

        brandstof = "-"
        transmissie = "-"

        prijs_match = re.search(
            r'€\s*([0-9\.\,]+)',
            tekst
        )

        if prijs_match:
            prijs = int(
                prijs_match.group(1)
                .replace(".", "")
                .replace(",", "")
            )

        km_match = re.search(
            r'([0-9\.]{2,10})\s*km',
            tekst,
            re.IGNORECASE
        )

        if km_match:

            kmstand = int(
                km_match.group(1)
                .replace(".", "")
            )

        bouwjaar_matches = re.findall(
            r'\b(20[0-2][0-9])\b',
            tekst
        )

        if bouwjaar_matches:
            bouwjaar = int(
                bouwjaar_matches[0]
            )

        if "benzine" in tekst.lower():
            brandstof = "Benzine"

        if (
            "handgeschakeld"
            in tekst.lower()
        ):
            transmissie = "Handgeschakeld"

        # Extra controles

        if prijs and prijs > MAX_PRIJS:
            continue

        if kmstand and kmstand > MAX_KM:
            continue

        if bouwjaar and bouwjaar < MIN_BOUWJAAR:
            continue

        if brandstof != "Benzine":
            continue

        if transmissie != "Handgeschakeld":
            continue

        geldige_advertenties.append({

            "titel": titel,
            "prijs": prijs,
            "km": kmstand,
            "bouwjaar": bouwjaar,
            "brandstof": brandstof,
            "transmissie": transmissie,
            "url": advertentie_url

        })

    except Exception as e:

        print(
            "Fout bij advertentie:",
            e
        )

if geldige_advertenties:

    kaarten = ""

    for auto in geldige_advertenties:

        prijs_text = (
            f"€ {auto['prijs']:,}"
            .replace(",", ".")
            if auto["prijs"]
            else "-"
        )

        km_text = (
            f"{auto['km']:,} km"
            .replace(",", ".")
            if auto["km"]
            else "-"
        )

        bouwjaar_text = (
            str(auto["bouwjaar"])
            if auto["bouwjaar"]
            else "-"
        )

        kaarten += f"""
        <div style="
            border:1px solid #d5d5d5;
            border-radius:12px;
            padding:16px;
            margin-bottom:18px;
            background:#fafafa;
        ">

            <h2 style="
                margin-top:0;
                color:#0066cc;
            ">
                🚗 {auto['titel']}
            </h2>

            <table style="
                font-size:15px;
                line-height:1.8;
            ">

                <tr>
                    <td><b>💰 Prijs</b></td>
                    <td>{prijs_text}</td>
                </tr>

                <tr>
                    <td><b>📅 Bouwjaar</b></td>
                    <td>{bouwjaar_text}</td>
                </tr>

                <tr>
                    <td><b>🛣️ Kilometerstand</b></td>
                    <td>{km_text}</td>
                </tr>

                <tr>
                    <td><b>⛽ Brandstof</b></td>
                    <td>{auto['brandstof']}</td>
                </tr>

                <tr>
                    <td><b>⚙️ Transmissie</b></td>
                    <td>{auto['transmissie']}</td>
                </tr>

            </table>

            <p>
                {auto['url']}
                    Bekijk advertentie op AutoScout24
                </a>
            </p>

        </div>
        """

    html = f"""
    <html>

    <body style="
        font-family:Arial,sans-serif;
        max-width:900px;
    ">

        <h1 style="color:#0066cc;">
            🚗 Nieuwe Seat Leon advertenties
        </h1>

        <p>
            Er zijn vandaag
            <strong>
                {len(geldige_advertenties)}
            </strong>
            nieuwe advertenties gevonden.
        </p>

        <p>
            Filters:
        </p>

        <ul>
            <li>Seat Leon</li>
            <li>Benzine</li>
            <li>Handgeschakeld</li>
            <li>Zwart</li>
            <li>Bouwjaar vanaf 2016</li>
            <li>Max €12.500</li>
            <li>Max 150.000 km</li>
        </ul>

        {kaarten}

        <hr>

        <p style="color:#888;">
            Automatisch verstuurd door jouw
            GitHub Auto Agent.
        </p>

    </body>
    </html>
    """

    msg = MIMEText(
        html,
        "html",
        "utf-8"
    )

    msg["Subject"] = (
        f"🚗 {len(geldige_advertenties)} nieuwe Seat Leon advertentie(s)"
    )

    msg["From"] = EMAIL
    msg["To"] = EMAIL

    server = smtplib.SMTP(
        "smtp.gmail.com",
        587
    )

    server.starttls()

    server.login(
        EMAIL,
        PASSWORD
    )

    server.send_message(msg)

    server.quit()

    with open(
        "seen_ads.txt",
        "a",
        encoding="utf-8"
    ) as f:

        for link in sorted(nieuwe_links):
            f.write(link + "\n")

    print("Mail verzonden")

else:

    print("Geen nieuwe advertenties")
