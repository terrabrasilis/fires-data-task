## Preparation of fire focuses data

Automation or semi-automation to prepare data of fire spots for the panel of focuses versus deforestation areas and CAR's rural real estate base.

The implementation follows the step by step described in the file ./docs/step-by-step-description.txt.

The expected periodicity is monthly for the acquisition of new data on the focuses of the Queimadas project and notices of deforestation by the DETER project.


### Table to control the data acquisition process

CREATE TABLE public.acquisition_data_control
(
    id integer NOT NULL DEFAULT nextval('acquisition_data_control_id_seq'::regclass),
    start_date date,
    end_date date,
    num_rows integer,
    origin_data character varying(80) COLLATE pg_catalog."default",
    CONSTRAINT acquisition_data_control_id_pk PRIMARY KEY (id)
);