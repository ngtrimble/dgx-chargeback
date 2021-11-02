from logzero import logger
import paramiko
from scp import SCPClient
import time
import timeout_decorator
import os

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
        self._scp = None
        self._passwd = None
        self._group = None
        
        try:
            logger.info("Connecting to SSH Server: " + hostname)
            self._client.connect(hostname, port, username, password)
            logger.info("Sucessfully connected to SSH Server: " + hostname)
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to connect to SSH Server")

        try:
            logger.info("Setting up SCP Connection: " + hostname)
            self._scp = SCPClient(self._client.get_transport())
            logger.info("Sucessfully set up SCP Connection: " + hostname)
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to setup SCP Connection")

    def __del__(self):
        """
        Close the SSH Connection
        """

        try:
            logger.info("Closing connection to SSH Server: " + self._host)
            self._scp.close()
            self._client.close()
        except:
            logger.warning("Failed to cleanly close the SSH Connection")
            pass

        try:
            logger.info("Cleaning up temporary files: " + self._host)
            os.remove('/tmp/passwd')
            os.remove('/tmp/group')
        except:
            logger.warning("Failed to cleanup temporary files")
            pass

    @timeout_decorator.timeout(60, timeout_exception=TimeoutError, exception_message="SCP Timeout (60 seconds)")
    def getUsersAndGroups(self):
        """
        Get the /etc/passwd and /etc/group files, and store them in lists
        """

        logger.info("Collecting /etc/passwd and /etc/group from SSH Host")

        try:
            self._scp.get('/etc/passwd','/tmp/passwd')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/passwd file with SCP")

        if os.path.isfile('/tmp/passwd'):
            with open('/tmp/passwd') as f:
                self._passwd  = f.read().splitlines()
        else:
            raise Exception("Failed to read contents of passwd, /tmp/passwd does not exist")

        try:
            self._scp.get('/etc/group','/tmp/group')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/group file with SCP")

        if os.path.isfile('/tmp/group'):
            with open('/tmp/group') as f:
                self._group  = f.read().splitlines()
        else:
            raise Exception("Failed to read contents of group, /tmp/group does not exist")

        if not self._passwd:
            raise Exception("passwd is empty")

        if not self._group:
            raise Exception("group is empty")

        logger.debug("Found '{}' users in /etc/passwd, and '{}' groups in /etc/group".format(len(self._passwd),len(self._group)))


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