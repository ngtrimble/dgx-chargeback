from logzero import logger
import paramiko
import time
import timeout_decorator

__author__ = "Kalen Peterson"
__version__ = "0.2.5"
__license__ = "MIT"

class Ssh:

    def __init__(self, hostname, port, username, password):
        """
        Initialize the Connection to SSH Server
        """
        self._host = hostname
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

        try:
            logger.info("Connecting to SSH Server: " + hostname)
            self._client.connect(hostname, port, username, password)
            logger.info("Sucessfully connected to SSH Server: " + hostname)
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to connect to SSH Server")

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

    @timeout_decorator.timeout(30, timeout_exception=TimeoutError, exception_message="SSH Timeout (30 seconds)")
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
            raise Exception('Failed to map UID to user')

    @timeout_decorator.timeout(30, timeout_exception=TimeoutError, exception_message="SSH Timeout (30 seconds)")
    def mapUidtoGroups(self, uid):
        """
        Connect to the host and map a UID to a list of member groups
        """

        # Run the SSH Command and decode the response
        stdin, stdout, stderr = self._client.exec_command("id -Gn " + str(uid))
        error = stderr.read().decode('ascii').strip('\n')
        groups = stdout.read().decode('ascii').strip('\n')

        if not error:
            groupList = groups.split(" ")
            return groupList
        else:
            logger.error(error)
            raise Exception('Failed to get Group list from UID')