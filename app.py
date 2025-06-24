from flask import Flask, request, render_template, redirect, session
from flask_mail import Mail, Message
import os
import uuid
import csv
from datetime import datetime
import requests  # new, for reCAPTCHA verification
import logging  # new, for advanced logging

logging.basicConfig(level=logging.INFO)  # Setup basic logging

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "geheime_sleutel")  # Voor sessies

# ✅ Secure Gmail SMTP Configuration
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME'),
    MAIL_DEBUG=False,  # Disable debug mode for production
)

mail = Mail(app)

# ✅ Dummy materiaal_data updated for demonstration with additional materials
materiaal_data = {
    'hout': 10,
    'metaal': 20,
    'kunststof': 5,
    'beton': 50,
    'tegel': 15,
    'glas': 40,
    'isolatie': 8
}

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

            # ✅ Sessie logging
            if 'session_id' not in session:
                session['session_id'] = str(uuid.uuid4())

            log_dir = "logs"
            os.makedirs(log_dir, exist_ok=True)
            log_file = os.path.join(log_dir, f"{session['session_id']}.csv")

            with open(log_file, mode='a', newline='') as file:
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

        except Exception as e:
            foutmelding = str(e)

    return render_template('index.html', resultaat=resultaat, foutmelding=foutmelding, materialen=materiaal_data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    """Render contact page and process contact form submissions with reCAPTCHA validation."""
    success = False
    error_msg = None

    if request.method == 'POST':
        # Honeypot spam prevention
        honeypot = request.form.get('honeypot')
        if honeypot:
            error_msg = "Spam detectie: formulier ongeldig ingevuld."
            return render_template('contact.html', success=success, error_msg=error_msg, recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'))
        
        # reCAPTCHA validation
        captcha_response = request.form.get('g-recaptcha-response')
        recaptcha_secret = os.environ.get('RECAPTCHA_SECRET')
        if not captcha_response or not recaptcha_secret:
            error_msg = "Captcha validatie mislukt: token of secret ontbreekt."
            return render_template('contact.html', success=success, error_msg=error_msg, recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'))
        captcha_data = {
            'secret': recaptcha_secret,
            'response': captcha_response,
            'remoteip': request.remote_addr
        }
        captcha_verify = requests.post("https://www.google.com/recaptcha/api/siteverify", data=captcha_data)
        if not captcha_verify.json().get('success'):
            error_msg = "Captcha validatie mislukt. Probeer het opnieuw."
            return render_template('contact.html', success=success, error_msg=error_msg, recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'))

        email = request.form.get('email')
        message = request.form.get('message')
        if not email or not message:
            error_msg = "Zorg ervoor dat zowel e-mailadres als bericht zijn ingevuld."
            return render_template('contact.html', success=success, error_msg=error_msg, recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'))

        msg = Message("Nieuw contactbericht", recipients=["stoutengijs@gmail.com"])
        msg.body = f"From: {email}\n\n{message}"
        msg.reply_to = email
        msg.sender = app.config.get("MAIL_DEFAULT_SENDER")
        try:
            mail.send(msg)
            success = True
            logging.info("Email sent successfully.")
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo" in error_msg:
                error_msg += " | Controleer of MAIL_SERVER correct is ingesteld en bereikbaar is."
            logging.error("Mail sending failed: %s", e)

    return render_template('contact.html', success=success, error_msg=error_msg, recaptcha_site_key=os.environ.get('RECAPTCHA_SITE_KEY'))

@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')

if __name__ == '__main__':
    app.run(debug=True)
