#!/bin/bash
TARGET="alerts"
OUTPUT_TABLE=$deteroutputtable
# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom,classname, view_date, sensor, areamunkm) "
INSERT=$INSERT"SELECT geometries as geom, classname, date as view_date, sensor, areamunkm FROM $TARGET "
# drop the intermediary table
DROP_MONTH_TABLE="DROP TABLE $TARGET"
# exec process
. ./import_data.sh