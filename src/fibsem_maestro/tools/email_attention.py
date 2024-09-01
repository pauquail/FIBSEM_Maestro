# -*- coding: utf-8 -*-
"""
Created on Tue Jun 11 10:31:42 2024

@author: pavel
"""

# Gmail setting:
# https://stackoverflow.com/questions/10147455/how-to-send-an-email-with-gmail-as-provider-using-python/27515833#27515833

import os
import smtplib


def send_email(sender, receiver, subject, text, password_file="email_password.txt"):
    if os.path.exists(password_file):
        with open(password_file) as f:
            password = f.readline()
    else:
        print(f"{password_file} not found.")
        return

    if sender is not None and receiver is not None:
        print("Sending email.")
        smtpserver = smtplib.SMTP_SSL('smtp.gmail.com', 465)
        smtpserver.ehlo()
        smtpserver.login(sender, password)

        # Test send mail
        email_text = f'Subject: {subject}\n\n {text}'
        smtpserver.sendmail(sender, receiver, email_text)

        # Close the connection
        smtpserver.close()
