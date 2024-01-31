## Preparation of fire focuses data

***Used to load and processing data for fires dashboard**

Automation or semi-automation to prepare data of active fire for the panel of focuses versus deforestation areas and CAR's rural real estate base.

The implementation follows the step by step described in the file ./docs/step-by-step-description.txt.

The expected periodicity is monthly for the acquisition of new data on the focuses of the Queimadas project and notices of deforestation by the DETER project.

***WARNING***

Downloading Focuses of fire data has been disabled in favor of the [general-fires-data-task](https://github.com/terrabrasilis/general-fires-data-task).
Focus data is copied by import_focuses.sh using a SQL view.


## Configurations

There are three configuration files and a control table to prepare the execution environment, as follows:

 - config/deter_view_date (The DETER date reference, used to delimit the boundary between DETER and PRODES deforestation data)
 - config/gsconfig (user and password settings for GeoServer - DETER and Queimadas)
 - config/pgconfig (database settings to import and process data)
 - public.acquisition_data_control (a control table for imported data)

### Config details

 > Content of gsconfig file
```txt
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


 > SQL View to load focuses from raw_fires_data database
```sql
CREATE OR REPLACE VIEW public.raw_fires_data_online
 AS
SELECT id,
    focos.datahora,
    focos.satelite,
    focos.pais,
    focos.estado,
    focos.municipio,
    focos.bioma,
    focos.diasemchuva,
    focos.precipitacao,
    focos.riscofogo,
    focos.latitude,
    focos.longitude,
    focos.frp,
    focos.field_13,
    focos.classe_prodes,
    focos.classe_car,
    focos.data,
    focos.geom,
    focos.imported_at
    FROM dblink('hostaddr=<hostname or IP> port=5432 dbname=raw_fires_data user=postgres password=postgres'::text,
    'SELECT id, datahora, satelite, pais, estado, municipio, bioma, diasemchuva, precipitacao, riscofogo, latitude,
    longitude, frp, field_13, classe_prodes, classe_car, data, geom, imported_at
    FROM public.focos_aqua_referencia'::text)
    focos(id integer, datahora character varying, satelite character varying, pais character varying, estado character varying,
    municipio character varying, bioma character varying, diasemchuva integer, precipitacao double precision, riscofogo double precision,
    latitude double precision, longitude double precision, frp double precision, field_13 character varying, classe_prodes character varying,
    classe_car character varying, data date, geom geometry, imported_at date);
```