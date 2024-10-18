## Preparation of fire focuses data

***Used to load and processing data for fires dashboard**

Automation or semi-automation to prepare data of active fire for the panel of focuses versus deforestation areas and CAR's rural property base.

The implementation follows the step by step described in the file ./docs/step-by-step-description.txt.

The expected periodicity is monthly for the acquisition of new data on the focuses of the Queimadas project and notices of deforestation by the DETER projects.

***WARNING***

Downloading Focuses of fire data has been disabled in favor of the [general-fires-data-task](https://github.com/terrabrasilis/general-fires-data-task).
Focus data is copied by copy_data.py using a SQL view.


## Configurations

There are two configuration files and a control table to prepare the execution environment, as follows:

 - config/pgconfig (database settings used by GDAL to rasterize vector data from database)
 - config/db.cfg (database settings used to copy data and store the classify results)
 - public.acquisition_data_control (a control table to register the copied data)

### Runtime Settings

The DETER date reference, used to delimit the boundary between DETER and PRODES deforestation data.

Use the environment variable, DETER_VIEW_DATE=yyyy-mm-dd, to define the referency date to copy data from DETER databases.

 > into Docker compose or Docker stack
```yaml
    environment:
        DETER_VIEW_DATE: '2023-08-01'
```


#### Configuration files details

 > Content of pgconfig file
```txt
user="postgres"
password="postgres"
host=localhost
port=5432
dbname=fires_dashboard
```

 > Content of db.cfg file
```txt
[fires_dashboard]
host: <hostname or IP>
port: 5432
user: postgres
password: postgres
dbname: fires_dashboard

[raw_fires_data]
host: <hostname or IP>
port: 5432
user: postgres
password: postgres
dbname: raw_fires_data

[deter_amazonia]
host: <hostname or IP>
port: 5432
user: postgres
password: postgres
dbname: deter_amazonia

[deter_cerrado]
host: <hostname or IP>
port: 5432
user: postgres
password: postgres
dbname: deter_cerrado

[deter_pantanal]
host: <hostname or IP>
port: 5432
user: postgres
password: postgres
dbname: deter_pantanal
```

### Database requirements


 > Table to control the data acquisition process
```sql
CREATE TABLE public.acquisition_data_control
(
    id serial NOT NULL,
    start_date date,
    end_date date,
    num_rows integer,
    origin_data character varying(80),
    created_at date DEFAULT (now())::date,
    CONSTRAINT acquisition_data_control_id_pk PRIMARY KEY (id)
);
```
