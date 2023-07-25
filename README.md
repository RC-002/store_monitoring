# This is a Flask application for the Store Management take-home assignment

## Tech-stack

1. Back-end
    - Python
    - Flask
    - XML

2. Front-end
    - HTML
    - CSS
    - JS
    - JQuery
    - AJAX

3. Database
    - The application can use any SQL Database, but during development postgreSQL was used.

## High-Level Design:

1. Front-end, back-end and file-store communication
    ![image](https://github.com/RC-002/store_monitoring/assets/83537305/a0588aa1-2e68-4667-9b0c-b60d9e45b034)


2. Back-end and DB communication
    ![image](https://github.com/RC-002/store_monitoring/assets/83537305/8642de4b-0632-48ba-9063-9a3a114e3f61)


## Set-up

1. A virtual enviromnent can be set up:
     - Open terminal and go to the directory of this flask application
     - Create a venv using
        ```
        python3 -m venv <name of virtual env>
        ```    
    - goto venv
        ```
        cd .\venv\Scripts\
        ```
    - Start activate.bat
        ```
        ./activate
        ```
2. Install all the packages in the requirement.txt file
```
pip install -r requirements.txt
```

3. Create the following schema in any DB 
     - ```
       1. menu_hours
        (
        	store_id - big integer
        	day - varchar
        	start_time_local - time without tz	
        	end_time_local - time without tz
        )

       2. process_report
        (
        	report_id - varchar
        	status - varchar
        )

        3. store_timezones
        (
        	store_id - big integer
        	timezone_str - varchar
        )

       4. store_status
        (
        	store_id - big integer
        	status - varchar
        	timestamp_utc - timestamp with tz
        )
       ```

4. In the env folder, rename the config_fill.xml file to config.xml and fill in the DB config details.
5. For convenience, to push the code on GitHub the CSV files (in csv_files/) are empty. Append the rows to these files as needed.

## Run the application

Start the server using the command
```
flask run
```

## Design Considerations

1. All the variables and routes in the flask application use camelCase
2. All the tables and column names use snake_case
3. In the flask application, there are 2 .py files that separate the logic of the utility functions and the route handlers themselves – Separation of concerns
4. The DB connection parameters and the config settings are external (env/config.xml). This can be used to change the configs to move easily between dev, prod, and testing.  


