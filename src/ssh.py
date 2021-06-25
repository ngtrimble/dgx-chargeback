from logzero import logger
import base64
import paramiko

class Ssh:

    def __init__(self, hostname, port, username, password):
        """
        Initialize the Connection to SSH Server
        """
        self._host = hostname
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        logger.info("Connecting to SSH Server: " + hostname)
        self._client.connect(hostname, port, username, password)

    def __del__(self):
        """
        Close the SSH Connection
        """

        try:
            logger.info("Closing connection to SSH Server: " + self._host)
            self._client.close()
        except:
            logger.warning("Failed to cleanly close the SSH Connection")
            pass

    def mapUidtoUsername(self, uid):
        """
        Connect to the host and map a UID to Username
        """

        # Run the SSH Command and decode the response
        stdin, stdout, stderr = self._client.exec_command("id -nu " + str(uid))
        error = stderr.read().decode('ascii').strip('\n')
        user = stdout.read().decode('ascii').strip('\n')
        
        if not error:
            return str(user)
        else:
            logger.error(error)
            raise ValueError('Failed to map UID to user')