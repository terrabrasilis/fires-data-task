#!/bin/bash
TARGET="focuses"
OUTPUT_TABLE="focos_aqua_referencia"
# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom, datahora, satelite, pais, estado, municipio, bioma, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data) "
INSERT=$INSERT"SELECT geometries as geom, data_hora_::text as datahora, satelite, pais, estado, municipio, bioma, numero_dia as diasemchuva, precipitac as precipitacao, risco_fogo as riscofogo, latitude, longitude, frp, data_hora_::date as data FROM $TARGET "
# drop the intermediary table
DROP_MONTH_TABLE="DROP TABLE $TARGET"
# exec process
. ./import_data.sh