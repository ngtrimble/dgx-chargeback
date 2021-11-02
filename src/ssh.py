from logzero import logger
import paramiko
from scp import SCPClient
import time
import timeout_decorator
import os

__author__ = "Kalen Peterson"
__version__ = "0.3.0"
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
            logger.warning("Failed to cleanup temporary files. This is OK")
            pass

    @timeout_decorator.timeout(60, timeout_exception=TimeoutError, exception_message="SCP Timeout (60 seconds)")
    def getUsersAndGroups(self):
        """
        Get the /etc/passwd and /etc/group files, and store them in lists
        """

        logger.info("Collecting /etc/passwd and /etc/group from SSH Host")

        # Get /etc/passwd
        try:
            self._scp.get('/etc/passwd','/tmp/passwd')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/passwd file with SCP")

        # Parse /etc/passwd
        if os.path.isfile('/tmp/passwd'):
            with open('/tmp/passwd') as f:
                self._passwd  = f.read().splitlines()
        else:
            raise Exception("Failed to read contents of passwd, /tmp/passwd does not exist")

        # Get /etc/group
        try:
            self._scp.get('/etc/group','/tmp/group')
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to get /etc/group file with SCP")

        # Parse /etc/group
        if os.path.isfile('/tmp/group'):
            with open('/tmp/group') as f:
                self._group  = f.read().splitlines()
        else:
            raise Exception("Failed to read contents of group, /tmp/group does not exist")

        # Validate passwd and group
        if not self._passwd:
            raise Exception("passwd is empty")

        if not self._group:
            raise Exception("group is empty")

        logger.debug("Found '{}' users in /etc/passwd, and '{}' groups in /etc/group".format(len(self._passwd),len(self._group)))


    def mapUidtoUsername(self, uid):
        """
        Map the UID to Username via the collected /etc/passwd file
        """

        username = None
        for line in self._passwd:
            split_line = line.split(':')
            user_id = str(split_line[2])
            user_name = str(split_line[0])

            if user_id == str(uid):
                username = user_name
                break
        
        if username:
            return str(username)
        else:
            raise Exception('Failed to map UID to user')

    def mapUsernametoGroups(self, username):
        """
        Map the Username to a list of member groups via the collected /etc/group file
        """

        groups = []
        for line in self._group:
            split_line = line.split(':')
            group_name = str(split_line[0])
            group_members = str(split_line[3])

            if group_members:
                split_group_members = group_members.split(',')
                if str(username) in split_group_members:
                    groups.append(group_name)

        if groups:
            return groups
        else:
            raise Exception('Failed to map UID to member groups')