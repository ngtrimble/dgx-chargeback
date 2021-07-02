from logzero import logger
import smtplib
from email.mime.text import MIMEText

__author__ = "Kalen Peterson"
__version__ = "0.1.0"
__license__ = "MIT"

class Email:

    def __init__(self, username, password, host, port, mailFrom, mailTo):
        """
        Setup the SMTP Connection
        """
        self._username = username
        self._password = password
        self._host = host
        self._port = port
        self._from = mailFrom
        self._to = mailTo

    def sendSuccess(self):
        """
        Send a Successfully Completee Email
        """
        reciever = "A Test User <to@example.com>"
        sender = "Private Person <from@example.com>"
        msg = MIMEText("The DGX Chargeback process ran successfully.")
        msg['Subject'] = 'DGX Chargeback Success'
        msg['From'] = self._from
        msg['To'] = self._to
    
        logger.info("Sending Success Email notification")
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:

            if self._username and self._password:
                server.login(self._username, self._password)

            server.sendmail(sender, reciever, msg.as_string())
            logger.debug("Sent Email")

    def sendFailure(self, error):
        """
        Send an exception Email
        """
        reciever = "A Test User <to@example.com>"
        sender = "Private Person <from@example.com>"
        msg = MIMEText("The DGX Chargeback process faild to complete")
        msg['Subject'] = 'DGX Chargeback Failure'
        msg['From'] = self._from
        msg['To'] = self._to
    
        logger.info("Sending Success Email notification")
        with smtplib.SMTP("smtp.mailtrap.io", 2525) as server:

            if self._username and self._password:
                server.login(self._username, self._password)

            server.sendmail(sender, reciever, msg.as_string())
            logger.debug("Sent Email")

        