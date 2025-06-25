# Materiaalcalculator

Een gebruiksvriendelijke webapplicatie om snel de benodigde hoeveelheid materiaal en richtprijs te berekenen voor diverse bouwonderdelen.

## Features

- Selecteer bouwonderdeel en materiaal
- Voer afmetingen in (lengte, breedte, optioneel hoogte/helling)
- Automatische prijsberekening met marge
- Resultaten worden per sessie opgeslagen ** werkt nog niet naar behoren
- Contactformulier met e-mailnotificatie
- Overzicht van eigen berekeningen ** werkt nog niet naar behoren
- Moderne, responsieve interface

## Installatie

1. **Clone deze repository:**
   ```bash
   git https://github.com/HonNoMushii/END_PROJECT.git
   cd END_PROJECT
   ```

2. **Installeer de vereiste packages:**
   ```bash
   pip install -r requirements.txt
   ```

3. **Stel de benodigde omgevingsvariabelen in (bij gebruik van render.com):** 

   - `SECRET_KEY` (geheime sleutel voor Flask sessies)
   - `MAIL_USERNAME` (SMTP e-mailadres, bijv. Gmail)
   - `MAIL_PASSWORD` (SMTP wachtwoord of app-wachtwoord)
   - `PORT` (optioneel)

## Gebruik

- Ga naar https://end-project-8pek.onrender.com/.
- Vul de velden in en klik op **Bereken**.
- Bekijk je berekeningen via "Mijn Berekeningen".
- Neem contact op via het contactformulier.

## Mappenstructuur

```
END_PROJECT/
│
├── app.py
├── wsgi.py
├── requirements.txt
├── README.md
├── LICENSE
├── .gitignore
├── static/
│   └── style.css
├── templates/
│   ├── index.html
│   ├── contact.html
│   ├── info.html
│   └── mijn_berekeningen.html
└── logs/
```
## Licentie
MIT License — zie [LICENSE](LICENSE) voor details.
---
Vragen of feedback? Gebruik het contactformulier op de webpagina 