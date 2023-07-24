from flask import Flask, render_template, send_file, request
import pandas as pd
import csv
import sqlalchemy as sa
import psycopg2
import uuid
import json
import csv
from datetime import datetime,timedelta
from flask import send_file
from xml.dom import minidom

global properties

app = Flask(__name__)
#common funciton to get the DB Connection
def getDBConnection():
    global properties
    conn = psycopg2.connect(database = properties['database'],
                            user =  properties['user'], 
                            password =  properties['password'],
                            host =  properties['host'],
                            port =  int(properties['port']))
    return conn

def populateProps():
    global properties
    mydoc = minidom.parse('static\config.xml')
    items = mydoc.getElementsByTagName('item')
    properties = {items[0].attributes['name'].value: items[0].firstChild.data}
    properties.update({items[1].attributes['name'].value: items[1].firstChild.data})
    properties.update({items[2].attributes['name'].value: items[2].firstChild.data})
    properties.update({items[3].attributes['name'].value: items[3].firstChild.data})
    properties.update({items[4].attributes['name'].value: items[4].firstChild.data})

@app.route("/")
def hello_world():
    populateProps()
    return render_template('index.html')

# route to insert the Menu Hours data. this method reads the menuhours CSV and inserts into the menuhours DB table
@app.route("/upload/menuhours", methods = ['GET', 'POST'])
def uploadMenus():
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
    return "Successfully Processed the Menu Hours! Number of rows processed:" + str(rowcount)

# route to insert the Store Status data. this method reads the store CSV and inserts into the Store status DB table
@app.route("/upload/storestatus", methods = ['GET', 'POST'])
def uploadStoresStatus():
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
    return "Successfully Processed the Store Status data! Number of rows processed:" + str(rowcount)


# route to insert the Time zone data. this method reads the Time Zone CSV and inserts into the Time Zone DB table
@app.route("/upload/timezone", methods = ['GET', 'POST'])
def uploadTimeZone():
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
    return "Successfully Processed the Time Zone data! Number of rows processed:" + str(rowcount)


# route to process the Report at the Current Timestamp
@app.route("/trigger_report", methods = ['GET', 'POST'])
def triggerReport():
    conn = getDBConnection()
    cursor = conn.cursor()
    # Update a Inprogress Record in the DB.
    uuidStr = uuid.uuid4()
    print(uuidStr)
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
    result_set = cursor.fetchall()
    with open('static/result.csv', 'w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["store_id", "uptime_last_hour(in minutes)", "uptime_last_day(in hours)", "update_last_week(in hours)", "downtime_last_hour(in minutes)", "downtime_last_day(in hours)", "downtime_last_week(in hours)" ])
    for row in result_set:
        processStore(row[0], row[1], timezone, offset, cursor)
    # update the status back to the DB
    updateReportRecord = 'update public.processreport status = \'Complete\' where report_id = \''+str(uuidStr)+'\''
    cursor.execute(updateReportRecord)
    conn.commit()
    conn.close()
    return "report_id:"+ str(uuidStr)

# this methods is called for each store to Build hte store specific JSON
def processStore(store_id, timezone, clientTimezone, offset, cursor):
    # initialize all hte variables
    uptime_last_hour = 0
    uptime_last_day =0
    uptimelast_week =0
    downtime_last_hour =0 
    downtime_last_day =0 
    downtime_last_week =0
    # check if there is any data available for store in last 2 weeks.  
    selectAnyRecordsAvailable = 'select * from public.storestatus A  where (A.timestamp_utc >= date_trunc(\'week\', CURRENT_TIMESTAMP - interval \'2 week\') and A.timestamp_utc < date_trunc(\'week\', CURRENT_TIMESTAMP))'
    print(selectAnyRecordsAvailable)
    cursor.execute(selectAnyRecordsAvailable)    
    result_set = cursor.fetchall()
    rowsPresent = False
    for row in result_set:
        rowsPresent = True
    if (rowsPresent):
        # loop through for each Day from today for a week and caculate the downtime...
        values = range(7)
        currentDateTime = datetime.now()        
        weekday = currentDateTime.weekday()
        current_time = currentDateTime.strftime("%H:%M:%S")
        for dayValues in values:
            currentDate = currentDateTime - timedelta(days=dayValues)
            year_month_day_format = '%Y-%m-%d'
            formatDate = currentDate.strftime(year_month_day_format)  
            currentDateDayOfWeek = currentDate.weekday()
            selectMenuHours = 'select * from public.menuhours  where store_id='+str(store_id) +' and day = '+ str(currentDateDayOfWeek)
            cursor.execute(selectMenuHours)    
            result_set = cursor.fetchall()
            #get the Menu Hours of the store for the context day.
            startList=[]
            endList=[]
            for row in result_set:
                #endTime = row[3]
                startList.append(row[2])
                endList.append(row[3])
            #get the Activity status from the DB for the store and Date/Day
            selectStoreStatus = 'select A.status, A.timestamp_utc, B.timezone from public.storestatus A, (SELECT  timestamp_utc, timestamp_UTC AT TIME ZONE \''+timezone+'\' AT TIME ZONE  \'UTC\' FROM  public.storestatus A1 where store_id='+str(store_id)+') B where A.store_id= '+str(store_id)+' and A.timestamp_utc = B.timestamp_utc and timezone::date = date \''+formatDate+'\''
            #print(selectStoreStatus)
            cursor.execute(selectStoreStatus)    
            result_set = cursor.fetchall()
            activeList=[]
            inActiveList=[]

            for row in result_set:
                storeDateTime = row[2]
                storeTime = storeDateTime.time()
                #print(row[0])
                if row[0] == 'active':
                    activeList.append(storeTime)
                else:
                    inActiveList.append(storeTime)
            activeList.sort()
            inActiveList.sort()
            # calculate the Uptime and downtime for each hour, day and then for week
            for activeItem in activeList:
                onHours = False
                for i in range(len(startList)):
                    if (activeItem > startList[i]) & (activeItem < endList[i]):
                        onHours = True
                if (onHours):
                    #print('Good')
                    uptimelast_week = uptimelast_week+ 60;
                    if (dayValues==0):
                        uptime_last_day = uptime_last_day+ 60;
                        if ((current_time - activeItem) < 1 ):
                            uptime_last_hour = uptime_last_hour + 60
                #else:
                    #print('Bad')   
            for inActiveItem in inActiveList:
                onHours = False
                for i in range(len(startList)):
                    if (inActiveItem > startList[i]) & (inActiveItem < endList[i]):
                        onHours = True
                if (onHours):
                    #print('Good')
                    downtime_last_week = downtime_last_week+ 60;
                    if (dayValues==0):
                        downtime_last_day = downtime_last_day+ 60;  
                        if ((current_time - inActiveItem) < 1 ):
                            downtime_last_hour = downtime_last_hour + 60                   
                #else:
                    #print('Bad')                  
        #convert all the data into appropriate units
        uptimelast_week = uptimelast_week/60
        downtime_last_week = downtime_last_week/60
        uptime_last_day = uptime_last_day/60
        downtime_last_day = downtime_last_day/60
    # build CSV
    with open('static/result.csv', 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([store_id, uptime_last_hour, uptime_last_day, uptimelast_week, downtime_last_hour, downtime_last_day, downtime_last_week ])
    return 

# route to process the get Report, option is the report Id. Return Error for Invalid Report Id, Running if the status is running and the CSV for completed Files
@app.route("/get_report/<option>", methods = ['GET', 'POST'])
def get_report(option):
    conn = getDBConnection()
    cursor = conn.cursor()
    print(option)
    selectReport = 'select * from public.processreport A  where report_id = \''+option + '\''
    print(selectReport)
    cursor.execute(selectReport)
    status=''
    result_set = cursor.fetchall()
    for row in result_set:
        status = row[1]
    if (status ==  ''):
        return 'Invalid report Id' 
    if (status ==  'Complete'):    
        return send_file('static/result.csv','Report.csv')
    return status
 


if __name__ == "__main__":
    app.run(host='0.0.0.0', debug=True)