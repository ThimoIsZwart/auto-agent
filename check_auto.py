import os
import re
import json
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


def extract_car_data(html):

    result = {
        "titel": "Seat Leon",
        "prijs": None,
        "bouwjaar": None,
        "km": None,
        "kleur": None,
        "transmissie": None,
        "foto": None
    }

    matches = re.findall(
        r'<script type="application/ld\+json">(.*?)</script>',
        html,
        re.DOTALL
    )

    for match in matches:

        try:

            data = json.loads(match)

            if data.get("@type") != "Product":
                continue

            offers = data.get("offers", {})
            item = offers.get("itemOffered", {})

            result["prijs"] = offers.get("price")

            result["foto"] = item.get("image")

            result["kleur"] = item.get("color")

            result["transmissie"] = item.get(
                "vehicleTransmission"
            )

            result["titel"] = item.get(
                "name",
                "Seat Leon"
            )

            production_date = item.get(
                "productionDate"
            )

            if production_date:
                result["bouwjaar"] = production_date[:4]

            mileage = item.get(
                "mileageFromOdometer",
                {}
            )

            result["km"] = mileage.get("value")

            return result

        except Exception:
            pass

    return result


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

    if "seat-leon" not in link.lower():
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
            line.strip()
            for line in f
            if line.strip()
        )

else:
    gezien = set()

nieuwe_links = gevonden - gezien

print("Nieuw:", len(nieuwe_links))

autos = []

for advertentie_url in sorted(nieuwe_links):

    try:

        pagina = requests.get(
            advertentie_url,
            headers=HEADERS,
            timeout=30
        )

        data = extract_car_data(
            pagina.text
        )

        if data["prijs"]:

            if int(data["prijs"]) > MAX_PRIJS:
                continue

        if data["km"]:

            if int(data["km"]) > MAX_KM:
                continue

        if data["bouwjaar"]:

            if int(data["bouwjaar"]) < MIN_BOUWJAAR:
                continue

        if data["kleur"]:

            if "zwart" not in data["kleur"].lower():
                continue

        if data["transmissie"]:

            if "hand" not in data["transmissie"].lower():
                continue

        data["url"] = advertentie_url

        autos.append(data)

    except Exception as e:

        print(e)

if autos:

    kaarten = ""

    for auto in autos:

        prijs_text = "-"

        if auto["prijs"]:
            prijs_text = (
                f"€ {int(auto['prijs']):,}"
                .replace(",", ".")
            )

        km_text = "-"

        if auto["km"]:
            km_text = (
                f"{int(auto['km']):,} km"
                .replace(",", ".")
            )

        bouwjaar = auto["bouwjaar"] or "-"
        transmissie = auto["transmissie"] or "-"
        kleur = auto["kleur"] or "-"
        foto = auto["foto"] or ""

        kaarten += f"""
        <div style="
            border:1px solid #d9d9d9;
            border-radius:12px;
            padding:20px;
            margin-bottom:25px;
            background:#fafafa;
        ">

            {foto}

            <h2 style="
                color:#0d47a1;
                margin-top:0;
            ">
                🚗 {auto['titel']}
            </h2>

            <table style="
                font-size:15px;
                line-height:2;
            ">

                <tr>
                    <td><b>💰 Prijs</b></td>
                    <td>{prijs_text}</td>
                </tr>

                <tr>
                    <td><b>📅 Bouwjaar</b></td>
                    <td>{bouwjaar}</td>
                </tr>

                <tr>
                    <td><b>🛣️ Kilometerstand</b></td>
                    <td>{km_text}</td>
                </tr>

                <tr>
                    <td><b>⚙️ Transmissie</b></td>
                    <td>{transmissie}</td>
                </tr>

                <tr>
                    <td><b>🎨 Kleur</b></td>
                    <td>{kleur}</td>
                </tr>

            </table>

            <p style="margin-top:20px;">
                {auto['url']}
                    Bekijk advertentie
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

        <h1 style="color:#0d6efd;">
            🚗 Nieuwe Seat Leon advertenties
        </h1>

        <p>
            Er zijn
            <strong>{len(autos)}</strong>
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
            <li>Vanaf 2016</li>
            <li>Max €12.500</li>
            <li>Max 150.000 km</li>
        </ul>

        {kaarten}

        <hr>

        <p style="color:#777;">
            Automatisch gegenereerd door jouw GitHub Auto Agent.
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
        f"🚗 {len(autos)} nieuwe Seat Leon advertentie(s)"
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
