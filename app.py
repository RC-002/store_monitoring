# packages import
from flask import Flask, render_template, send_file, request
import csv
import uuid
import csv

# utility function import
from utility import *

app = Flask(__name__)

# Routes

# Route for the home page
@app.route("/")
def homePage():
    # Call the function to Populatr DB fields
    populateProps()
    return render_template('index.html')

# Route to insert the Menu Hours data. this method reads the menuhours CSV and inserts into the menuhours DB table
@app.route("/upload/menuhours", methods = ['GET', 'POST'])
def uploadMenus():
    # Get conn object and set cursor
    conn = getDBConnection()
    conn.autocommit = False
    cursor = conn.cursor()

    # First delete all the existing data and then insert the data.
    deleteSql = 'delete from public.menuhours'
    cursor.execute(deleteSql)    
    copySql = '''COPY public.menuhours(store_id,day,start_time_local,end_time_local)
    FROM 'C:\Loop\csv_files\Menu hours.csv'
    DELIMITER ','
    CSV HEADER;'''

    # get the total number of rows affected
    cursor.execute(copySql)
    rowcount = cursor.rowcount
    conn.commit()
    conn.close()

    # return the rowcount
    return "Successfully Processed the Menu Hours!\n{} number of rows processed:".format(str(rowcount))

# Route to insert the Store Status data. this method reads the store CSV and inserts into the Store status DB table
@app.route("/upload/storestatus", methods = ['GET', 'POST'])
def uploadStoresStatus():
    # Get conn object and set cursor
    conn = getDBConnection()
    conn.autocommit = False
    cursor = conn.cursor()

    # First delete all the existing data and then insert the data.
    deleteSql = 'delete from public.storestatus'
    cursor.execute(deleteSql)    
    copySql = '''COPY public.storestatus(store_id,status,timestamp_utc)
    FROM 'C:\Loop\csv_files\store status.csv'
    DELIMITER ','
    CSV HEADER;'''

    # get the total number of rows affected
    cursor.execute(copySql)
    rowcount = cursor.rowcount

    # Move the timestamp_utc to localtime 
    conn.commit()
    conn.close()

    # return the rowcount
    return "Successfully Processed the Store Status data!\n{} number of rows processed:".format(str(rowcount))


# Route to insert the Time zone data. this method reads the Time Zone CSV and inserts into the Time Zone DB table
@app.route("/upload/timezone", methods = ['GET', 'POST'])
def uploadTimeZone():
    # Get conn object and set cursor
    conn = getDBConnection()
    conn.autocommit = False
    cursor = conn.cursor()

    # First delete all the existing data and then insert the data.
    deleteSql = 'delete from public.timezone'
    cursor.execute(deleteSql)    
    copySql = '''COPY public.timezone(store_id,timezone_str)
    FROM 'C:\Loop\csv_files\Time zone.csv'
    DELIMITER ','
    CSV HEADER;'''
    
    # get the total number of rows affected
    cursor.execute(copySql)
    rowcount = cursor.rowcount
    conn.commit()
    conn.close()

    # return the rowcount
    return "Successfully Processed the Time Zone data!\n{} number of rows processed:".format(str(rowcount))


# Route to process the Report at the Current Timestamp
@app.route("/trigger_report", methods = ['GET', 'POST'])
def triggerReport():
    # Get conn object and set cursor
    conn = getDBConnection()
    cursor = conn.cursor()

    # Update a Inprogress Record in the DB.
    uuidStr = uuid.uuid4()
    insertReportRecord = 'insert into public.processreport (report_id, status) values (\''+ str(uuidStr)+'\', \'Running\')'
    print(insertReportRecord)
    cursor.execute(insertReportRecord)
    conn.commit()

    #initialize for processing.
    timezone = request.args.get('timezone')
    offset = request.args.get('offset')

    # get all the Stores from the Timezone Table...
    selectTimeZone = 'select * from public.timezone'
    cursor.execute(selectTimeZone)    
    resultSet = cursor.fetchall()

    # create csv file
    fileName = "download/{}.csv".format(str(uuidStr))
    with open(fileName, 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["store_id", "uptime_last_hour(in minutes)", "uptime_last_day(in hours)", "update_last_week(in hours)", "downtime_last_hour(in minutes)", "downtime_last_day(in hours)", "downtime_last_week(in hours)" ])
    for row in resultSet:
        processStore(row[0], row[1], timezone, offset, cursor, fileName)

    # update the status back to the DB
    updateReportRecord = 'update public.processreport status = \'Complete\' where report_id = \''+str(uuidStr)+'\''
    cursor.execute(updateReportRecord)
    conn.commit()
    conn.close()
    return str(uuidStr)



# Route to process the get Report, option is the report Id. Return Error for Invalid Report Id, Running if the status is running and the CSV for completed Files
@app.route("/get_report/<option>", methods = ['GET', 'POST'])
def get_report(option):
    # Get conn object and set cursor
    conn = getDBConnection()
    cursor = conn.cursor()
    selectReport = 'select * from public.processreport where report_id = \''+option + '\''
    cursor.execute(selectReport)
    status=''
    result_set = cursor.fetchall()

    for row in result_set:
        status = row[1]
        if (status ==  ''):
            return 'Invalid report Id' 
        if (status ==  'Complete'): 
            fileName = "download/{}.csv".format(str(option))  
            return send_file(fileName,'Report.csv')
    return status
 


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)