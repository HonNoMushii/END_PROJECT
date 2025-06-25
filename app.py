from flask import Flask, request, render_template, redirect, session
from flask_mail import Mail, Message
import os
import uuid
import csv
from datetime import datetime
import json
import logging
import re
from collections import defaultdict

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "geheime_sleutel")  # Session security

# Configure mail settings
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME'),
    MAIL_DEBUG=False,
)

mail = Mail(app)

# Basis materiaaldata
materiaal_data = {
    # Basis
    'hout': 10,
    'metaal': 20,
    'kunststof': 5,
    'beton': 50,
    'tegel': 15,
    'glas': 40,
    'isolatie': 8,

    # Constructie & structuur
    'baksteen': 35,
    'betonblokken': 27,
    'gewapend beton': 65,
    'cellenbeton': 28,
    'kalkzandsteen': 32,
    'ytong blokken': 30,
    'staalconstructie': 55,
    'funderingsbeton': 60,
    'staalnetwapening': 12,

    # Houtsoorten
    'vurenhout': 12,
    'hardhout': 40,
    'osb-platen': 18,
    'multiplex': 25,
    'underlayment': 22,
    'mdf-platen': 20,

    # Binnenafwerking
    'gipsplaat': 12,
    'cement': 18,
    'laminaat': 20,
    'parket': 40,
    'tapijt': 15,
    'kurkvloer': 28,
    'vinyl vloer': 18,
    'pleisterwerk': 10,
    'systeemplafond': 25,
    'verf': 6,
    'behang': 8,
    'keramische tegels': 35,
    'sierpleister': 14,
    'akoestisch plafond': 45,

    # Isolatie
    'dakisolatie': 20,
    'vloerisolatie': 15,
    'wandisolatie': 18,
    'cellulose-isolatie': 20,
    'pir-isolatie': 25,
    'eps-isolatie': 15,
    'minerale wol': 18,
    'houtvezelisolatie': 28,
    'reflecterende folie': 12,

    # Energie & duurzaamheid
    'zonnepanelen': 150,
    'zonneboilerpanelen': 110,
    'warmtepomp': 120,
    'groendak': 45,
    'leemstuc': 22,
    'bamboevloer': 26,
    'leemstenen': 34,
    'vlasisolatie': 21,
    'zonneboiler': 110,
    'regenwaterpomp': 75,

    # Techniek & installaties
    'leidingen': 10,
    'elektra': 15,
    'vloerverwarming': 50,
    'radiatoren': 35,
    'ventilatie': 18,
    'rookmeldersysteem': 5,
    'domotica bekabeling': 15,
    'bekabeling': 10,
    'schakelmateriaal': 8,
    'data/utp bekabeling': 6,
    'groepenkast': 140,
    'pv-omvormer': 90,

    # Sanitair & badkamer
    'badkamertegels': 40,
    'douchewand glas': 70,
    'kitwerk': 4,
    'waterdichte folie': 12,
    'inloopdouchevloer': 75,
    'sanitair wandframe': 60,
    'tegelmatjes mozaïek': 55,

    # Buitenruimte & tuin
    'grind': 12,
    'klinkers': 22,
    'tuinbestrating luxe': 40,
    'vlonderplanken': 30,
    'graszoden': 6,
    'boomschorsbedekking': 6,
    'schuttinghout': 30,
    'tuinverlichting': 10,
    'regenwateropvang': 25,
    'betontegels': 18,
    'natuursteen tegels': 45,
    'grindmatten': 16,
    'tuinhekken': 35,
    'kantopsluiting beton': 12
}


# In-memory statistiek
app.config["materiaal_stats"] = defaultdict(int)

@app.route('/', methods=['GET', 'POST'])
def index():
    resultaat = None
    foutmelding = None
    onderdeel = request.values.get('onderdeel')

    if request.method == 'POST':
        try:
            materiaal = request.form.get('materiaal')
            marge = float(request.form.get('marge', 0)) / 100
            eenheid = request.form.get('eenheid', 'm')
            conversie = {'mm': 0.001, 'cm': 0.01, 'm': 1.0}
            factor = conversie.get(eenheid, 1.0)

            if materiaal not in materiaal_data:
                foutmelding = "Onbekend materiaal geselecteerd."
                return render_template('index.html', foutmelding=foutmelding, materialen=materiaal_data)

            try:
                lengte = float(request.form.get('lengte', '').strip()) * factor
                breedte = float(request.form.get('breedte', '').strip()) * factor
                hoogte_raw = request.form.get('hoogte', '').strip()
                hoogte = float(hoogte_raw) * factor if hoogte_raw else 0
                helling_raw = request.form.get('helling', '').strip()
                helling = float(helling_raw) if helling_raw else None
            except Exception:
                foutmelding = "Ongeldige invoer voor lengte, breedte, hoogte of helling."
                return render_template('index.html', foutmelding=foutmelding, materialen=materiaal_data)

            base_result = lengte * breedte * (1 + marge) * materiaal_data[materiaal]
            resultaat = {
                'onderdeel': onderdeel,
                'materiaal': materiaal,
                'lengte': lengte,
                'breedte': breedte,
                'hoogte': hoogte if hoogte else None,
                'helling': helling,
                'marge': float(request.form.get('marge', 5)),
                'oppervlakte': round(lengte * breedte, 2),
                'aantal': round(base_result, 2),
                'eenheid': eenheid,
                'prijs': round(base_result * 1.5, 2)
            }

            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            datum = datetime.now().strftime('%Y%m%d')
            log_csv = os.path.join(log_dir, f"{session['session_id']}_{datum}.csv")
            log_json = os.path.join(log_dir, f"{session['session_id']}_{datum}.jsonl")

            # CSV logging
            with open(log_csv, mode='a', newline='') as file:
                writer = csv.writer(file)
                writer.writerow([
                    datetime.now().isoformat(),
                    onderdeel,
                    materiaal,
                    lengte,
                    breedte,
                    hoogte,
                    helling,
                    eenheid,
                    resultaat['oppervlakte'],
                    resultaat['aantal'],
                    resultaat['prijs']
                ])

            # JSONL logging
            with open(log_json, 'a') as jf:
                json.dump(resultaat, jf)
                jf.write('\n')

            # Statistiek bijhouden
            app.config["materiaal_stats"][materiaal] += 1
            logging.info(f"Gebruik materiaal: {materiaal} | Totaal: {app.config['materiaal_stats'][materiaal]}")

        except Exception as e:
            foutmelding = str(e)

    return render_template('index.html', resultaat=resultaat, foutmelding=foutmelding, materialen=materiaal_data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    error_msg = None

    if request.method == 'POST':
        email = request.form.get('email')
        message = request.form.get('message')

        if not email or not re.match(r"[^@]+@[^@]+\.[^@]+", email):
            error_msg = "Ongeldig of ontbrekend e-mailadres."
            return render_template('contact.html', success=success, error_msg=error_msg)

        if not message:
            error_msg = "Bericht mag niet leeg zijn."
            return render_template('contact.html', success=success, error_msg=error_msg)

        msg = Message("Nieuw contactbericht", recipients=["stoutengijs@gmail.com"])
        msg.body = f"From: {email}\n\n{message}"
        msg.reply_to = email
        msg.sender = app.config.get("MAIL_DEFAULT_SENDER")
        try:
            mail.send(msg)
            success = True
            logging.info("Email succesvol verzonden.")
        except Exception as e:
            error_msg = str(e)
            logging.error("Mail verzenden mislukt: %s", e)

    return render_template('contact.html', success=success, error_msg=error_msg)

@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')

@app.route('/mijn-berekeningen')
def mijn_berekeningen():
    if 'session_id' not in session:
        return "Geen actieve sessie."

    datum = datetime.now().strftime('%Y%m%d')
    log_json = os.path.join('logs', f"{session['session_id']}_{datum}.jsonl")

    resultaten = []
    if os.path.exists(log_json):
        with open(log_json) as f:
            for line in f:
                resultaten.append(json.loads(line))

    return render_template('mijn_berekeningen.html', resultaten=resultaten)


# Custom error handlers
@app.errorhandler(404)
def page_not_found(e):
    logging.warning(f"404 fout - URL: {request.path}")
    return "Pagina niet gevonden (404)", 404

@app.errorhandler(500)
def internal_server_error(e):
    logging.error(f"500 fout: {str(e)}")
    return "Interne serverfout (500)", 500

# Run app
if __name__ == '__main__':
    app.run(debug=True)
