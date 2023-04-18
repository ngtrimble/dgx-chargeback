from logzero import logger
import paramiko
from scp import SCPClient
import timeout_decorator
import os
import pwd
import grp

__author__ = "Kalen Peterson"
__version__ = "0.5.0"
__license__ = "MIT"

class Ssh:

    @timeout_decorator.timeout(30, timeout_exception=TimeoutError, exception_message="SSH Timeout (30 seconds)")
    def __init__(self, hostname, port, username, password):
        """
        Initialize the Connection to SSH Server
        """
        self._host = hostname
        self._client = paramiko.SSHClient()
        self._client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
        self._scp = None
        
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

    @timeout_decorator.timeout(60, timeout_exception=TimeoutError, exception_message="SCP Timeout (60 seconds)")
    def getUsersAndGroups(self):
        """
        Copy the /etc/passwd and /etc/group files to local container
        """

        logger.info("Collecting /etc/passwd and /etc/group from SSH Host")

        # Get /etc/passwd
        try:
            self._scp.get('/etc/passwd','/etc/passwd')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/passwd file with SCP")

        # Get /etc/group
        try:
            self._scp.get('/etc/group','/etc/group')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/group file with SCP")

    def mapUidtoUsername(self, uid):
        """
        Map the UID to Username via the collected /etc/passwd file
        """

        username = None
        user_record = pwd.getpwuid(uid)
        username = user_record.pw_name

        if username:
            logger.debug("Mapped UID '{}' to Username '{}'".format(uid, username))
            return str(username)
        else:
            raise Exception('Failed to map UID to user')

    def mapUsernametoGroups(self, username):
        """
        Map the Username to a list of member groups via the collected /etc/group file
        """

        groups = []
        user_record = pwd.getpwnam(username)
        gid = user_record.pw_gid
        groups = [grp.getgrgid(g).gr_name for g in os.getgrouplist(username, gid)]

        if groups:
            logger.debug("Mapped Username '{}' to Groups '{}'".format(username, ','.join(groups)))
            return groups
        else:
            raise Exception('Failed to map UID to member groups')