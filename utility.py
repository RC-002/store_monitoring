# packages import
import psycopg2
import csv
from datetime import datetime,timedelta
from xml.dom import minidom

global properties

# Utility Functions

# Funciton to get the DB Connection
def getDBConnection():
    global properties

    # define db connection object
    conn = psycopg2.connect(database = properties['database'],
                            user =  properties['user'], 
                            password =  properties['password'],
                            host =  properties['host'],
                            port =  int(properties['port']))
    return conn

# Function to Get ENV data from env/config.xml
def populateProps():
    global properties
    mydoc = minidom.parse('env/config.xml')
    items = mydoc.getElementsByTagName('item')
    properties = {items[0].attributes['name'].value: items[0].firstChild.data}
    properties.update({items[1].attributes['name'].value: items[1].firstChild.data})
    properties.update({items[2].attributes['name'].value: items[2].firstChild.data})
    properties.update({items[3].attributes['name'].value: items[3].firstChild.data})
    properties.update({items[4].attributes['name'].value: items[4].firstChild.data})

# Funtion that is called for each store to Build hte store specific JSON
def processStore(store_id, timezone, clientTimezone, offset, cursor, fileName):
    # initialize all the variables
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
    
    if len(result_set)>0:
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
                startList.append(row[2])
                endList.append(row[3])

            #get the Activity status from the DB for the store and Date/Day
            selectStoreStatus = 'select A.status, A.timestamp_utc, B.timezone from public.storestatus A, (SELECT  timestamp_utc, timestamp_UTC AT TIME ZONE \''+timezone+'\' AT TIME ZONE  \'UTC\' FROM  public.storestatus A1 where store_id='+str(store_id)+') B where A.store_id= '+str(store_id)+' and A.timestamp_utc = B.timestamp_utc and timezone::date = date \''+formatDate+'\''
            
            cursor.execute(selectStoreStatus)    
            result_set = cursor.fetchall()
            activeList=[]
            inActiveList=[]

            for row in result_set:
                storeDateTime = row[2]
                storeTime = storeDateTime.time()

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
                    uptimelast_week = uptimelast_week+ 60
                    if (dayValues==0):
                        uptime_last_day = uptime_last_day+ 60
                        if ((current_time - activeItem) < 1 ):
                            uptime_last_hour = uptime_last_hour + 60
                            
            for inActiveItem in inActiveList:
                onHours = False
                for i in range(len(startList)):
                    if (inActiveItem > startList[i]) & (inActiveItem < endList[i]):
                        onHours = True
                if (onHours):
                    downtime_last_week = downtime_last_week+ 60
                    if (dayValues==0):
                        downtime_last_day = downtime_last_day+ 60  
                        if ((current_time - inActiveItem) < 1 ):
                            downtime_last_hour = downtime_last_hour + 60       

        #convert all the data into appropriate units
        uptimelast_week = uptimelast_week/60
        downtime_last_week = downtime_last_week/60
        uptime_last_day = uptime_last_day/60
        downtime_last_day = downtime_last_day/60

    # build CSV
    with open(fileName, 'a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([store_id, uptime_last_hour, uptime_last_day, uptimelast_week, downtime_last_hour, downtime_last_day, downtime_last_week ])
    
    return 