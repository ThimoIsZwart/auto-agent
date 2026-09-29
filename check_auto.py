import os
import re
import json
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import requests
from bs4 import BeautifulSoup

# --- CONFIGURATIE & CRITERIA ---
MAX_PRIJS = 12500
MAX_KM = 150000
MIN_BOUWJAAR = 2016
EMAIL_USER = os.environ.get("EMAIL_USER")
EMAIL_PASSWORD = os.environ.get("EMAIL_PASSWORD")
RECEIVER_EMAIL = EMAIL_USER  # Stuur melding naar jezelf

SEEN_ADS_FILE = "seen_ads.txt"

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
}

def laad_geziene_ads():
    if os.path.exists(SEEN_ADS_FILE):
        with open(SEEN_ADS_FILE, "r") as f:
            return set(line.strip() for line in f if line.strip())
    return set()

def sla_geziene_ad_op(url):
    with open(SEEN_ADS_FILE, "a") as f:
        f.write(f"{url}\n")

# --- 1. AUTOSCOUT24 SCRAPER ---
def haal_autoscout_autos():
    url = "https://www.autoscout24.nl/lst/seat/leon?atype=C&ustate=N%2CU&sort=age&desc=1"
    gevonden_autos = []
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=15)
        if response.status_code != 200:
            print(f"AutoScout24 status code: {response.status_code}")
            return gevonden_autos

        soup = BeautifulSoup(response.text, "html.parser")
        links = set()
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/aanbod/" in href and "seat-leon" in href.lower():
                full_url = "https://www.autoscout24.nl" + href if href.startswith("/") else href
                links.add(full_url.split("?")[0])

        for link in links:
            try:
                ad_res = requests.get(link, headers=HEADERS, timeout=10)
                if ad_res.status_code != 200:
                    continue
                
                # Probeer JSON-LD uit te lezen
                scripts = re.findall(r'<script type="application/ld\+json">(.*?)</script>', ad_res.text, re.DOTALL)
                ad_data = {}
                for script in scripts:
                    try:
                        data = json.loads(script)
                        if isinstance(data, dict) and data.get("@type") in ["Car", "Vehicle", "Product"]:
                            ad_data = data
                            break
                    except json.JSONDecodeError:
                        continue

                titel = ad_data.get("name", "Seat Leon")
                
                # Prijs
                offers = ad_data.get("offers", {})
                prijs = int(offers.get("price", 0)) if isinstance(offers, dict) else 0
                
                km = 0
                bouwjaar = 0
                kleur = "Onbekend"
                transmissie = "Onbekend"
                foto = ""

                if "image" in ad_data:
                    foto = ad_data["image"][0] if isinstance(ad_data["image"], list) else ad_data["image"]

                km_match = re.search(r'(\d[\d\.]*)\s*km', ad_res.text, re.IGNORECASE)
                if km_match:
                    km = int(km_match.group(1).replace(".", ""))

                jaar_match = re.search(r'(20\d{2})', ad_res.text)
                if jaar_match:
                    bouwjaar = int(jaar_match.group(1))

                if "zwart" in ad_res.text.lower() or "black" in ad_res.text.lower():
                    kleur = "Zwart"
                if "handgeschakeld" in ad_res.text.lower() or "handschaltung" in ad_res.text.lower():
                    transmissie = "Handgeschakeld"

                gevonden_autos.append({
                    "titel": titel,
                    "url": link,
                    "prijs": prijs,
                    "km": km,
                    "bouwjaar": bouwjaar,
                    "transmissie": transmissie,
                    "kleur": kleur,
                    "foto": foto,
                    "bron": "AutoScout24"
                })
            except Exception as e:
                print(f"Fout bij uitlezen AutoScout link {link}: {e}")

    except Exception as e:
        print(f"Fout bij ophalen AutoScout24: {e}")

    return gevonden_autos

# --- 2. VAKGARAGE SCRAPER ---
def haal_vakgarage_autos():
    url = f"https://www.vakgarage.nl/occasions?merk%5B%5D=SEAT&model%5BSEAT%5D%5B%5D=Leon&prijs=%3B{MAX_PRIJS}&tellerstand=%3B{MAX_KM}&bouwjaar={MIN_BOUWJAAR}%3B&sort=created_at_desc"
    gevonden_autos = []
    
    headers = {
        **HEADERS,
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Referer": "https://www.vakgarage.nl/"
    }

    try:
        response = requests.get(url, headers=headers, timeout=15)
        if response.status_code != 200:
            print(f"Vakgarage status code: {response.status_code}")
            return gevonden_autos

        soup = BeautifulSoup(response.text, "html.parser")
        
        for a in soup.find_all("a", href=True):
            href = a["href"]
            if "/occasions/" in href and href != "/occasions":
                full_url = "https://www.vakgarage.nl" + href if href.startswith("/") else href
                
                if any(auto["url"] == full_url for auto in gevonden_autos):
                    continue

                gevonden_autos.append({
                    "titel": "Seat Leon",
                    "url": full_url,
                    "prijs": 0,       # De zoek-URL filtert al vooraf op de site zelf
                    "km": 0,
                    "bouwjaar": MIN_BOUWJAAR,
                    "transmissie": "Onbekend",
                    "kleur": "Onbekend",
                    "foto": "",
                    "bron": "Vakgarage"
                })

    except Exception as e:
        print(f"Fout bij ophalen Vakgarage: {e}")

    return gevonden_autos

# --- 3. E-MAIL VERZENDEN ---
def stuur_email(goedgekeurde_autos):
    if not EMAIL_USER or not EMAIL_PASSWORD:
        print("E-mail credentials ontbreken in de omgevingsvariabelen.")
        return

    kaarten = ""
    for auto in goedgekeurde_autos:
        foto_html = f'<img src="{auto["foto"]}" style="max-width:100%; border-radius:6px; margin-bottom:15px;">' if auto["foto"] else ''
        prijs_text = f"€ {auto['prijs']:,}".replace(",", ".") if auto["prijs"] else "Zie website"
        km_text = f"{auto['km']:,} km".replace(",", ".") if auto["km"] else "Zie website"

        kaarten += f"""
        <div style="border: 1px solid #ddd; padding: 20px; border-radius: 8px; margin-bottom: 25px;">
            {foto_html}
            <h2 style="color:#0d47a1; margin-top:0; margin-bottom:15px;">
                🚗 {auto['titel']} ({auto['bron']})
            </h2>
            <table style="font-size:15px; line-height:2;">
                <tr>
                    <td><b>💰 Prijs</b></td>
                    <td>{prijs_text}</td>
                </tr>
                <tr>
                    <td><b>📅 Bouwjaar</b></td>
                    <td>{auto['bouwjaar']}</td>
                </tr>
                <tr>
                    <td><b>🛣️ Kilometerstand</b></td>
                    <td>{km_text}</td>
                </tr>
                <tr>
                    <td><b>⚙️ Transmissie</b></td>
                    <td>{auto['transmissie']}</td>
                </tr>
                <tr>
                    <td><b>🎨 Kleur</b></td>
                    <td>{auto['kleur']}</td>
                </tr>
            </table>
            <div style="margin-top:20px;">
                <a href="{auto['url']}" style="background:#0d6efd; color:white; padding:10px 20px; text-decoration:none; border-radius:5px; display:inline-block;">
                    Bekijk advertentie
                </a>
            </div>
        </div>
        """

    html = f"""
    <html>
    <body style="font-family:Arial,sans-serif; max-width:900px;">
        <h1 style="color:#0d6efd;">
            🚗 Nieuwe Seat Leon advertenties
        </h1>
        <p>
            Er zijn <strong>{len(goedgekeurde_autos)}</strong> nieuwe advertenties gevonden.
        </p>
        <p>Criteria:</p>
        <ul>
            <li>Seat Leon</li>
            <li>Benzine</li>
            <li>Handgeschakeld</li>
            <li>Zwart</li>
            <li>Vanaf {MIN_BOUWJAAR}</li>
            <li>Max €{MAX_PRIJS:,}</li>
            <li>Max {MAX_KM:,} km</li>
        </ul>

        {kaarten}

        <hr>
    </body>
    </html>
    """

    msg = MIMEMultipart("alternative")
    msg["Subject"] = f"🚗 {len(goedgekeurde_autos)} Nieuwe Seat Leon(s) gevonden!"
    msg["From"] = EMAIL_USER
    msg["To"] = RECEIVER_EMAIL
    msg.attach(MIMEText(html, "html"))

    try:
        with smtplib.SMTP("smtp.gmail.com", 587) as server:
            server.starttls()
            server.login(EMAIL_USER, EMAIL_PASSWORD)
            server.sendmail(EMAIL_USER, RECEIVER_EMAIL, msg.as_string())
        print("E-mail succesvol verzonden!")
    except Exception as e:
        print(f"Fout bij versturen e-mail: {e}")

# --- HOOFDPROGRAMMA ---
def main():
    print("Seat Leon Agent gestart...")
    geziene_ads = laad_geziene_ads()

    alle_kandidaten = haal_autoscout_autos() + haal_vakgarage_autos()
    print(f"Totaal opgehaald: {len(alle_kandidaten)} advertenties")

    goedgekeurde_autos = []

    for auto in alle_kandidaten:
        url = auto["url"]
        
        if url in geziene_ads:
            continue

        sla_geziene_ad_op(url)
        geziene_ads.add(url)

        # Filters toepassen
        if auto["prijs"] and auto["prijs"] > MAX_PRIJS:
            continue
        if auto["km"] and auto["km"] > MAX_KM:
            continue
        if auto["bouwjaar"] and auto["bouwjaar"] < MIN_BOUWJAAR:
            continue
        if auto["kleur"] != "Onbekend" and "zwart" not in auto["kleur"].lower():
            continue
        if auto["transmissie"] != "Onbekend" and "hand" not in auto["transmissie"].lower():
            continue

        goedgekeurde_autos.append(auto)

    if goedgekeurde_autos:
        print(f"{len(goedgekeurde_autos)} nieuwe matching advertentie(s) gevonden! E-mail sturen...")
        stuur_email(goedgekeurde_autos)
    else:
        print("Geen nieuwe geschikte advertenties gevonden.")

if __name__ == "__main__":
    main()
