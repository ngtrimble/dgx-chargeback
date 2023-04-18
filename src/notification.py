from logzero import logger
from envelope import Envelope
from pathlib import Path
import timeout_decorator

__author__ = "Kalen Peterson"
__version__ = "0.5.0"
__license__ = "MIT"

class Email:

    def __init__(self, username, password, host, port, mailFrom, mailTo):
        """
        Setup the SMTP Connection
        """
        self._mail = Envelope()\
            .from_(mailFrom)\
            .to(mailTo)

        logger.info("Setting up SMTP Connection")
        if username and password:
            logger.info("Username and Password provided, SMTP authentication will be used")
            self._mail.smtp(host, port, username, password)
        else:
            logger.info("No Username and Password provided, SMTP authentication will not be used")
            self._mail.smtp(host, port)

    @timeout_decorator.timeout(30, timeout_exception=TimeoutError, exception_message="SMTP Send Timeout (30 seconds)")
    def _send(self):
        """
        Send a mail object and check the result
        """
        logger.info("Attempting to send Email")
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
            .message("The DGX Chargeback process ran successfully and inserted '%s' completed jobs.\n See attached log for details." % (len(insertedRecords)))\
            .attach(Path(logfile))

        self._send()

    def sendFailureReport(self, logfile):
        """
        Send an exception Email
        """
        self._mail\
            .subject("DGX Chargeback Failure")\
            .message("The DGX Chargeback process failed to complete.\nSee attached log for details.")\
            .attach(Path(logfile))

        self._send()

