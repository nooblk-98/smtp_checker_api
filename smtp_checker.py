from flask import Flask, request, jsonify
import smtplib
from email.message import EmailMessage

app = Flask(__name__)

@app.route('/check-smtp', methods=['POST'])
def check_smtp():
    data = request.json

    smtp_server = data.get('smtp_server')
    smtp_port = int(data.get('smtp_port', 587))
    username = data.get('username')
    password = data.get('password')
    from_email = data.get('from_email')
    to_email = data.get('to_email')

    msg = EmailMessage()
    msg.set_content("This is a test email for SMTP validation.")
    msg['Subject'] = "SMTP Test"
    msg['From'] = from_email
    msg['To'] = to_email

    try:
        with smtplib.SMTP(smtp_server, smtp_port, timeout=10) as server:
            server.starttls()
            server.login(username, password)
            server.send_message(msg)
        return jsonify({"status": "pass", "message": "Email sent successfully"})
    except Exception as e:
        return jsonify({"status": "fail", "error": str(e)})

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
