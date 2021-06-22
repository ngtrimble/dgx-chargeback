from logzero import logger
import mysql.connector


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
                                               host=host, port=port, database=database)
        except mysql.connector.Error as err:
            if err.errno == errorcode.ER_ACCESS_DENIED_ERROR:
                logger.error("Something is wrong with your user name or password")
            elif err.errno == errorcode.ER_BAD_DB_ERROR:
                logger.error("Database does not exist")
            else:
                logger.error(err)

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

    def writeManyQuery(self, query):
        """
        Run a set of MySQL Queries at once, returning the number of rows effected
        """
        cursor = self._cnx.cursor()
        cursor.execute(query)


class SlurmDb(MySqlDb):

    def __init__(self, slurmClusterName, *args, **kwargs):
        """
        Initialize the SlrumDB Connection
        """
        super().__init__(*args, **kwargs)
        self._jobTable = str(slurmClusterName + '_job_table')
        logger.info("My Job Table is " + self._jobTable)
    

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
            "gres_req",
            "gres_used"
        ])

        query = "SELECT " + fields + " FROM " + self._jobTable + " WHERE time_end BETWEEN %s AND %s"
        params = (
            startDate,
            endDate
        )

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

    def addChargebackJob (self):
        """
        Insert a completed Job into the Chargeback DB
        """
        fields = ", ".join([
            "slurm_job_name",
            "slurm_id_job",
            "time_start",
            "time_end",
            "duration_sec",
            "cpus_req",
            "exit_code",
            "user_id",
            "group_id",
            "user_name",
            "group_name",
            "nodelist",
            "node_alloc",
            "slurm_job_state",
            "job_result",
            "gpus_requested",
            "gpus_used"
        ])

        values = ", ".join([
            "slurm-job-99",
            "99",
            "2021-06-01 12:12:12.000",
            "2021-06-01 12:12:13.000",
            "1",
            "2",
            "0",
            "1",
            "1",
            "kalen",
            "kalen-group",
            "dgx-1",
            "1",
            "5",
            "success",
            "2",
            "2"
        ])

        fieldReplacers = ''
        for field in fields:
            fieldReplacers += "%s,"

        query = "INSERT INTO " + self._chargebackTable + " (" + fields + ") VALUES (" + values + ")"
        params = (
            values
        )

        logger.info(query)
        logger.info(params)
        result = self.writeManyQuery(query)

        return result