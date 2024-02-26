import smtplib
from email.mime.text import MIMEText

# Set up the email parameters
def confirmation_mail(rec_email, subject, message):
    sender_email = "harish7299152036@gmail.com"
    receiver_email = rec_email
    subject = subject
    message = message

    # Create a MIMEText object
    msg = MIMEText(message)

    # Set the sender and receiver email addresses, and the subject
    msg["From"] = sender_email
    msg["To"] = receiver_email
    msg["Subject"] = subject

    # Connect to the SMTP server
    with smtplib.SMTP("smtp.gmail.com", 587) as server:
        server.starttls()
        server.login(sender_email, 'apbjwxhcnfytqixv')  # Note: For security reasons, use environment variables or a configuration file for your password
        server.sendmail(sender_email, receiver_email, msg.as_string())
