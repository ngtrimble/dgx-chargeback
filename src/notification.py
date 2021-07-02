from logzero import logger
from envelope import Envelope
from pathlib import Path

__author__ = "Kalen Peterson"
__version__ = "0.1.1"
__license__ = "MIT"

class Email:

    def __init__(self, username, password, host, port, mailFrom, mailTo):
        """
        Setup the SMTP Connection
        """
        self._mail = Envelope()\
            .from_(mailFrom)\
            .to(mailTo)

        if username and password:
            self._mail.smtp(host, port, username, password)
        else:
            self._mail.smtp(host, port)

    def _send(self):
        """
        Send a mail object and check the result
        """
        result = self._mail.send()

        if bool(result):
            logger.info("Successfully sent email")
        else:
            logger.error(str(result))
            logger.error("Failed to send email")

    def sendSuccessReport(self, insertedRecords, logfile):
        """
        Send a Successfully Completed Email
        """

        self._mail\
            .subject("DGX Chargeback Success")\
            .message("The DGX Chargeback process ran successfully and inserted '%s' completed jobs. \n See attached log for details." % (len(insertedRecords)))\
            .attach(Path(logfile))

        self._send()

    def sendFailureReport(self, logfile):
        """
        Send an exception Email
        """
        self._mail\
            .subject("DGX Chargeback Failure")\
            .message("The DGX Chargeback process faild to complete. See attached log for details.")\
            .attach(Path(logfile))

        self._send()

