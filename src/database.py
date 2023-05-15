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
            "account",
            "`partition`"
        ])

        # Select all Jobs
        #  - time_end: In the specified UNIX Timestamp range
        #  - time_start: Greater than 0. If it is 0, the job was never executed.
        query = "SELECT " + fields + " FROM " + self._jobTable + " WHERE (time_end BETWEEN %s AND %s) AND time_start > 0"
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
            "acct",
            "is_def"
        ])

        # Get user associations if the user field is not null, and the user is not deleted
        ## Get 'is_def' (is default) for filtering later
        query = "SELECT " + fields + " FROM " + self._assocTable + " WHERE user <> '' AND deleted = 0"
        params = None

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)
        print(result)
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

            # Escape the partition colume. It is reserved
            #  TODO: this needs to be implemented generically to make all fields safe
            #        Plan to update this method to escape all input to the query.
            if key == 'partition':
                key = "`{}`".format(key)
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

    def getUserJobsInMonthRange (self, username, months, min_job_duration_sec):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "duration_sec",
            "gpus_used",
            "job_result"
        ])

        # Hardcode min year to 2020. This resolves some existing issues where time_start is set to 1970
        query = "SELECT " + fields + " FROM " + self._chargebackTable + " WHERE duration_sec >= %s AND user_name = %s AND (time_end >= (CURDATE() - INTERVAL %s MONTH )) AND YEAR(time_start) > 2020"
        params = (
            min_job_duration_sec,
            username,
            months
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    
    def getGroupJobsInMonthRange (self, groupname, months, min_job_duration_sec):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "duration_sec",
            "gpus_used",
            "job_result"
        ])

        # Hardcode min year to 2020. This resolves some existing issues where time_start is set to 1970
        query = "SELECT " + fields + " FROM " + self._chargebackTable + " WHERE duration_sec >= %s AND group_name = %s AND (time_end >= (CURDATE() - INTERVAL %s MONTH )) AND YEAR(time_start) > 2020"
        params = (
            min_job_duration_sec,
            groupname,
            months
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    
    def getUserJobsThisMonth (self, username, min_job_duration_sec):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "duration_sec",
            "gpus_used",
            "job_result"
        ])

        # Hardcode min year to 2020. This resolves some existing issues where time_start is set to 1970
        query = ("SELECT " + fields + " FROM " + self._chargebackTable + " "
                 "WHERE duration_sec >= %s "
                 "AND user_name = %s "
                 "AND MONTH(time_end) = MONTH(CURDATE()) "
                 "AND YEAR(time_end) = YEAR(CURDATE()) "
                 "AND YEAR(time_start) > 2020")
        params = (
            min_job_duration_sec,
            username
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
    
    def getGroupJobsThisMonth (self, groupname, min_job_duration_sec):
        """
        Get all jobs with time_end in a range
        """
        fields = ", ".join([
            "duration_sec",
            "gpus_used",
            "job_result"
        ])

        # Hardcode min year to 2020. This resolves some existing issues where time_start is set to 1970
        query = ("SELECT " + fields + " FROM " + self._chargebackTable + " "
                 "WHERE duration_sec >= %s "
                 "AND group_name = %s "
                 "AND MONTH(time_end) = MONTH(CURDATE()) "
                 "AND YEAR(time_end) = YEAR(CURDATE()) "
                 "AND YEAR(time_start) > 2020")
        params = (
            min_job_duration_sec,
            groupname
        )

        logger.debug(query)
        logger.debug(params)
        result = self.readQuery(query, params)

        return result
