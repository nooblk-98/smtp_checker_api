import os
import smtplib
import socket
import ssl
from email.message import EmailMessage
from flask import Flask, request, jsonify

app = Flask(__name__)

@app.route('/check-smtp', methods=['POST'])
def check_smtp():
    if not request.is_json:
        return jsonify({
            "status": "fail",
            "error": "Content-Type must be application/json"
        }), 400

    data = request.get_json(silent=True) or {}

    smtp_server = (data.get('smtp_server') or '').strip()
    smtp_port = int(data.get('smtp_port', 587))
    username = (data.get('username') or '').strip() or None
    password = data.get('password')
    from_email = (data.get('from_email') or '').strip() or None
    to_email = (data.get('to_email') or '').strip() or None

    # Optional controls
    send_email = bool(data.get('send_email', True))
    use_ssl = bool(data.get('use_ssl', smtp_port == 465))
    starttls = bool(data.get('starttls', not use_ssl))
    timeout = float(data.get('timeout', 10))
    subject = (data.get('subject') or 'SMTP Test').strip()
    message_body = (data.get('message') or 'This is a test email for SMTP validation.').strip()

    # Basic validation
    if not smtp_server:
        return jsonify({"status": "fail", "error": "smtp_server is required"}), 400
    if send_email and (not from_email or not to_email):
        return jsonify({"status": "fail", "error": "from_email and to_email are required when send_email=true"}), 400
    if username and password is None:
        return jsonify({"status": "fail", "error": "password is required when username is provided"}), 400

    # Compose message if needed
    msg = None
    if send_email:
        msg = EmailMessage()
        msg.set_content(message_body)
        msg['Subject'] = subject
        msg['From'] = from_email
        msg['To'] = to_email

    details = {
        "server": smtp_server,
        "port": smtp_port,
        "used_ssl": False,
        "used_starttls": False,
        "authenticated": False,
        "sent": False,
    }

    try:
        context = ssl.create_default_context()

        if use_ssl:
            with smtplib.SMTP_SSL(smtp_server, smtp_port, timeout=timeout, context=context) as server:
                details["used_ssl"] = True
                server.ehlo()
                if username:
                    server.login(username, password)
                    details["authenticated"] = True
                if send_email and msg is not None:
                    server.send_message(msg)
                    details["sent"] = True
                else:
                    # Do a NOOP to verify connection stays healthy
                    server.noop()
        else:
            with smtplib.SMTP(smtp_server, smtp_port, timeout=timeout) as server:
                server.ehlo()
                if starttls:
                    # Only start TLS if supported, unless explicitly forced via starttls=True
                    if server.has_extn('starttls'):
                        server.starttls(context=context)
                        server.ehlo()
                        details["used_starttls"] = True
                    else:
                        return jsonify({
                            "status": "fail",
                            "error": "STARTTLS not supported by server",
                            "details": details
                        }), 502
                if username:
                    server.login(username, password)
                    details["authenticated"] = True
                if send_email and msg is not None:
                    server.send_message(msg)
                    details["sent"] = True
                else:
                    server.noop()

        return jsonify({"status": "pass", "message": "SMTP check succeeded", "details": details}), 200

    except smtplib.SMTPAuthenticationError as e:
        return jsonify({"status": "fail", "error": "Authentication failed", "details": details, "smtp_code": getattr(e, 'smtp_code', None), "smtp_error": getattr(e, 'smtp_error', None).decode('utf-8', 'ignore') if getattr(e, 'smtp_error', None) else None}), 401
    except (smtplib.SMTPConnectError, smtplib.SMTPServerDisconnected) as e:
        return jsonify({"status": "fail", "error": "Connection failed", "details": details, "reason": str(e)}), 502
    except smtplib.SMTPSenderRefused as e:
        return jsonify({"status": "fail", "error": "Sender refused", "details": details, "smtp_code": e.smtp_code, "smtp_error": e.smtp_error.decode('utf-8', 'ignore') if isinstance(e.smtp_error, (bytes, bytearray)) else str(e.smtp_error)}), 422
    except smtplib.SMTPRecipientsRefused as e:
        # e.recipients is a dict of recipient -> (code, resp)
        return jsonify({"status": "fail", "error": "Recipient refused", "details": details, "recipients": {k: (v[0], (v[1].decode('utf-8', 'ignore') if isinstance(v[1], (bytes, bytearray)) else str(v[1]))) for k, v in (e.recipients or {}).items()}}), 422
    except smtplib.SMTPDataError as e:
        return jsonify({"status": "fail", "error": "SMTP data error", "details": details, "smtp_code": e.smtp_code, "smtp_error": e.smtp_error.decode('utf-8', 'ignore') if isinstance(e.smtp_error, (bytes, bytearray)) else str(e.smtp_error)}), 502
    except smtplib.SMTPHeloError as e:
        return jsonify({"status": "fail", "error": "HELO/EHLO error", "details": details, "reason": str(e)}), 502
    except smtplib.SMTPNotSupportedError as e:
        return jsonify({"status": "fail", "error": "Operation not supported by server", "details": details, "reason": str(e)}), 502
    except (socket.timeout, socket.gaierror, OSError) as e:
        return jsonify({"status": "fail", "error": "Network error", "details": details, "reason": str(e)}), 502
    except Exception as e:
        return jsonify({"status": "fail", "error": "Unexpected error", "details": details, "reason": str(e)}), 500

@app.route('/healthz', methods=['GET'])
def healthz():
    return jsonify({"status": "ok"})


@app.route('/', methods=['GET'])
def root():
    return jsonify({
        "name": "smtp-checker-api",
        "endpoints": {
            "POST /check-smtp": "Check SMTP connectivity, auth, and optionally send",
            "GET /healthz": "Health check"
        }
    })


if __name__ == '__main__':
    host = os.getenv('APP_HOST', '0.0.0.0')
    port = int(os.getenv('APP_PORT', '5000'))
    debug = os.getenv('APP_DEBUG', 'false').lower() in ('1', 'true', 'yes')
    app.run(host=host, port=port, debug=debug)
