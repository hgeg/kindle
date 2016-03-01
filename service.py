#!/usr/bin/env python
from flask import Flask, request, render_template
from werkzeug.debug import DebuggedApplication
from flup.server.fcgi import WSGIServer
import requests, smtplib, time

from email.MIMEMultipart import MIMEMultipart
from email.MIMEBase import MIMEBase
from email import Encoders

from credentials import SENDER_EMAIL, SENDER_PASSWORD

app = Flask(__name__)
app.debug = True
app.wsgi_app = DebuggedApplication(app.wsgi_app, True)

censor = lambda s: "%s%s%s"%(s[0], (len(s)-2)*'*',s[-1])

@app.route('/kindle/')
def home():
    return render_template('index.html')

@app.route('/kindle/send/', methods=['POST'])
def send():
    status = ""
    try:
        device_email = request.form['email']
        status = "Invalid device e-mail"
        assert(device_email.endswith('@kindle.com'))
        status = "Invalid URL"
        url = request.form['url']
        pdfr = requests.get(url)
        pdf = pdfr.content

        status = "Error connecting email server"
        server = smtplib.SMTP('smtp.gmail.com:587')
        server.ehlo()
        server.starttls()
        server.login(SENDER_EMAIL,SENDER_PASSWORD)
        msg = MIMEMultipart()
        msg['Subject'] = 'convert'
        msg['From'] = SENDER_EMAIL
        msg['To'] = device_email

        status = "Email format error"
        part = MIMEBase('application', "octet-stream")
        part.set_payload(pdf)
        Encoders.encode_base64(part)
        try:
            filename = pdfr.url.rsplit('/',1)[-1]
        except:
            filename = 'doc-%d.pdf'%(int(time.time()))
        part.add_header('Content-Disposition', 'attachment; filename="%s"'%filename)

        msg.attach(part)
        server.sendmail(SENDER_EMAIL, device_email, msg.as_string())
        
        return render_template('index.html', status="ok", message="sent to %s as %s"%(device_email, filename))

    except Exception as e:
        return render_template('index.html', status="error", message=status)

if __name__ == '__main__':
   WSGIServer(app).run()
