import requests

url = "https://www.autoscout24.nl/lst/seat/leon/ft_benzine/tr_handgeschakeld/bc_zwart?priceto=12500&fregfrom=2016&cy=NL&damaged_listing=exclude&desc=0&kmto=150000&powertype=kw&sort=standard&ustate=N%2CU&atype=C&mcat=ma64mo15869"

response = requests.get(
    url,
    headers={
        "User-Agent": "Mozilla/5.0"
    }
)

print("Status:", response.status_code)

with open("pagina.html", "w", encoding="utf-8") as f:
    f.write(response.text)

print(response.text[:2000])
