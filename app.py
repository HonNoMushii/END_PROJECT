from flask import Flask, request, render_template, redirect
from flask_mail import Mail, Message
import os  # <-- important for reading environment variables

app = Flask(__name__)

# ✅ Secure Gmail SMTP Configuration using environment variables
app.config.update(
    MAIL_SERVER='smtp.gmail.com',
    MAIL_PORT=587,
    MAIL_USE_TLS=True,
    MAIL_USE_SSL=False,
    MAIL_USERNAME=os.environ.get('MAIL_USERNAME'),  # Your Gmail address
    MAIL_PASSWORD=os.environ.get('MAIL_PASSWORD'),  # Your App Password
    MAIL_DEFAULT_SENDER=os.environ.get('MAIL_USERNAME'),
    MAIL_DEBUG=True  # Set to False in production
)

mail = Mail(app)

# Dummy materiaal_data for demonstration
materiaal_data = {
    'hout': 10,
    'metaal': 20,
    'kunststof': 5
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

            if materiaal not in materiaal_data:
                foutmelding = "Onbekend materiaal geselecteerd."
                return render_template('index.html', foutmelding=foutmelding, materialen=materiaal_data)

            try:
                lengte = float(request.form.get('lengte', '').strip())
                breedte = float(request.form.get('breedte', '').strip())
                hoogte_raw = request.form.get('hoogte', '').strip()
                hoogte = float(hoogte_raw) if hoogte_raw else 0
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
                'eenheid': 'm²',
                'prijs': round(base_result * 1.5, 2)
            }
        except Exception as e:
            foutmelding = str(e)
    return render_template('index.html', resultaat=resultaat, foutmelding=foutmelding, materialen=materiaal_data)

@app.route('/contact', methods=['GET', 'POST'])
def contact():
    success = False
    error_msg = None

    if request.method == 'POST':
        # Optional basic spam prevention: honeypot field (hidden in HTML)
        honeypot = request.form.get('honeypot')
        if honeypot:
            error_msg = "Spam detectie: formulier ongeldig ingevuld."
            return render_template('contact.html', success=success, error_msg=error_msg)

        email = request.form.get('email')
        message = request.form.get('message')

        if not email or not message:
            error_msg = "Zorg ervoor dat zowel e-mailadres als bericht zijn ingevuld."
            return render_template('contact.html', success=success, error_msg=error_msg)

        msg = Message("Nieuw contactbericht", recipients=["stoutengijs@gmail.com"])
        msg.body = f"From: {email}\n\n{message}"
        msg.reply_to = email
        msg.sender = app.config.get("MAIL_DEFAULT_SENDER")

        print("Attempting to send email to stoutengijs@gmail.com...")
        try:
            mail.send(msg)
            success = True
            print("Email sent successfully.")
        except Exception as e:
            error_msg = str(e)
            if "getaddrinfo" in error_msg:
                error_msg += " | Controleer of MAIL_SERVER correct is ingesteld en bereikbaar is."
            print("Mail sending failed:", e)

    return render_template('contact.html', success=success, error_msg=error_msg)

@app.route('/info', methods=['GET'])
def info():
    return render_template('info.html')

if __name__ == '__main__':
    app.run(debug=True)
