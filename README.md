## Preparation of fire focuses data

***Used to load and processing data for fires dashboard**

Automation or semi-automation to prepare data of fire spots for the panel of focuses versus deforestation areas and CAR's rural real estate base.

The implementation follows the step by step described in the file ./docs/step-by-step-description.txt.

The expected periodicity is monthly for the acquisition of new data on the focuses of the Queimadas project and notices of deforestation by the DETER project.

## Configurations

There are three configuration files and a control table to prepare the execution environment, as follows:

 - config/deter_view_date (The DETER date reference, used to delimit the boundary between DETER and PRODES deforestation data)
 - config/gsconfig (user and password settings for GeoServer - DETER and Queimadas)
 - config/pgconfig (database settings to import and process data)
 - public.acquisition_data_control (a control table for imported data)

### Config details

 > Content of gsconfig file
```txt
FOCUSES_USER="user to login on geoserver of Queimadas."
FOCUSES_PASS="password to login on geoserver of Queimadas."
ALERTS_USER="user to login on geoserver of DETER."
ALERTS_PASS="password to login on geoserver of DETER."
```

 > Content of pgconfig file
```txt
user="postgres"
host="localhost"
port="5432"
database="fires_dashboard"
password="postgres"
deteroutputtable="deter"
firesoutputtable="focos_aqua_referencia"
```

 > Table to control the data acquisition process
```sql
CREATE TABLE public.acquisition_data_control
(
    id integer NOT NULL DEFAULT nextval('acquisition_data_control_id_seq'::regclass),
    start_date date,
    end_date date,
    num_rows integer,
    origin_data character varying(80) COLLATE pg_catalog."default",
    created_at date DEFAULT (now())::date,
    CONSTRAINT acquisition_data_control_id_pk PRIMARY KEY (id)
);
```