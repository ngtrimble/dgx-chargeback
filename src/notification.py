from logzero import logger
import smtplib

__author__ = "Kalen Peterson"
__version__ = "0.1.0"
__license__ = "MIT"

class Email:

    def __init__(self, username, password, host, port, mailFrom, maiTo):
        """
        Initialize the SMTP Connection
        """
        self._server = None
        self._host = host
        self._from = mailFrom
        self._to = mailTo

        self._server = smtplib.SMTP(host, port)
        self._server.login(username, password)


    def sendReport(self, report):

        self._server.sendmail(self._from, self._to, message)

    def sendSuccess(self)

    message = f"""\
    Subject: DGX Chargeback Success
    To: {reciever}
    From: {sender}

    The DGX Chargeback process ran successfully."""
    
    self._server.sendmail((self._from, self._to, message))