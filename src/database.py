from logzero import logger
import mysql.connector

__author__ = "Kalen Peterson"
__version__ = "0.5.0"
__license__ = "MIT"

class MySqlDb:

    def __init__(self, username, password, host, port, database):
        """
        Initialize the Connection to the MySQL DB
        """
        self._cnx = None
        self._host = host

        try:
            logger.info("Connecting to MySQL DB: " + host)
            self._cnx = mysql.connector.connect(user=username, password=password,
                                               host=host, port=port, database=database,
                                               get_warnings=True)
        except Exception as err:
            logger.error(err)
            raise Exception("Failed to connect to MySQL database")

    def __del__(self):
        """
        Close the DB Connection
        """
        try:
            logger.info("Closing connection to MySQL DB: " + self._host)
            self._cnx.close()
        except:
            logger.warning("Failed to cleanly close the MySQL Connection")
            pass

    def readQuery(self, query, params):
        """
        Run a simple MySQL Query and return the results as a dict
        """
        cursor = self._cnx.cursor()
        try:
            cursor.execute(query, params)
            columns = [column[0] for column in cursor.description]
            results = []
            for row in cursor.fetchall():
                results.append(dict(zip(columns, row)))

            return results
        finally:
            cursor.close()

    def insertQuery(self, query, params):
        """
        Run an insert query, returing the number of rows affected
        """
        cursor = self._cnx.cursor()
        try:
            cursor.execute(query, params)
            self._cnx.commit()
            count = cursor.rowcount

            return count
        finally:
            cursor.close()


class SlurmDb(MySqlDb):

    def __init__(self, slurmClusterName, *args, **kwargs):
        """
        Initialize the SlrumDB Connection
        """
        super().__init__(*args, **kwargs)
        self._jobTable = str(slurmClusterName + '_job_table')
        self._assocTable = str(slurmClusterName + '_assoc_table')
        logger.info("My Job Table is " + self._jobTable)
        logger.info("My Association Table is " + self._assocTable)
    
    def getJobsRange (self, startDate, endDate):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "job_name",
            "id_job",
            "time_start",
            "time_end",
            "cpus_req",
            "exit_code",
            "id_user",
            "id_group",
            "nodelist",
            "nodes_alloc",
            "state",
            "tres_req",
            "account"
        ])

        query = "SELECT " + fields + " FROM " + self._jobTable + " WHERE time_end BETWEEN %s AND %s"
        params = (
            startDate,
            endDate
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    
    def getAccountAssociations (self):
        """
        Get all User->Account associations
        """
        fields = ", ".join([
            "user",
            "acct"
        ])

        query = "SELECT " + fields + " FROM " + self._assocTable + " WHERE user <> ''"
        params = None

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result

class ChargebackDb(MySqlDb):
    
    def __init__(self, chargebackTable, *args, **kwargs):
        """
        Initialize the ChargebackDb Connection
        """
        super().__init__(*args, **kwargs)
        self._chargebackTable = str(chargebackTable)
        logger.info("My Job Table is " + self._chargebackTable)

    def addUniqueJob (self, record):
        """
        Insert a completed Job into the Chargeback DB, Must be a Uniuq Slurm Job ID
        """
        
        # Extract the Keys and Values (must corrospond to DB Columns)
        fields = []
        values = []
        for key, value in record.items():
            fields.append(key)
            values.append(value)

        # Generate MySQL Replacers
        fieldReplacers = ""
        for field in fields:
            fieldReplacers += "%s,"

        # Build and run Unique Check Query
        checkQuery = "SELECT slurm_id_job from " + self._chargebackTable + " WHERE slurm_id_job = %s"
        jobExists = self.readQuery(checkQuery, [record["slurm_id_job"]])

        # Build Insert Query
        fieldReplacers = fieldReplacers.strip(",")
        strFields = ", ".join(fields)
        insertQuery = "INSERT INTO " + self._chargebackTable + " (" + strFields + ") VALUES (" + fieldReplacers + ")"
       
        if not jobExists:

            logger.debug(insertQuery)
            logger.debug(values)
            result = self.insertQuery(insertQuery, values)
            logger.info("Updated: '" + str(result) + "' rows")
            return True

        else:
            logger.info("No Update needed, slurm_job_id=" + str(record["slurm_id_job"]) + " already exists")
            return False
        
    def getLatestJobs (self, limit):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "job_id",
            "slurm_job_name",
            "time_start",
            "time_end",
            "user_name"
        ])

        query = "SELECT " + fields + " FROM " + self._chargebackTable + " ORDER BY job_id DESC LIMIT %s"
        params = (
            limit,
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result

    def getUserJobsCompletedRange (self, username, months):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "job_id",
            "slurm_job_name",
            "duration_sec",
            "time_end",
            "gpus_used",
            "group_name",
            "user_name",
            "added"
        ])

        query = "SELECT " + fields + " FROM " + self._chargebackTable + " WHERE job_result = 'COMPLETED' AND user_name = %s AND (time_end >= (CURDATE() - INTERVAL %s MONTH ))"
        params = (
            username,
            months
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    
    def getGroupJobsCompletedRange (self, groupname, months):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "job_id",
            "slurm_job_name",
            "duration_sec",
            "time_end",
            "gpus_used",
            "group_name",
            "user_name",
            "added"
        ])

        query = "SELECT " + fields + " FROM " + self._chargebackTable + " WHERE job_result = 'COMPLETED' AND group_name = %s AND (time_end >= (CURDATE() - INTERVAL %s MONTH ))"
        params = (
            groupname,
            months
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    