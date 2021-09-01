#!/bin/bash
TARGET="alerts_amz"
OUTPUT_TABLE=$deteroutputtable
# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom,classname, view_date, sensor, areamunkm) "
INSERT=$INSERT"SELECT geometries as geom, classname, view_date, sensor, areamunkm FROM $TARGET "
# drop the intermediary table
DROP_MONTH_TABLE="DROP TABLE $TARGET"
# control of end
CTRL_ALERTS_AMZ=false
# exec process
. ./import_data.sh

TARGET="alerts_cerrado"
OUTPUT_TABLE=$deteroutputtable
# copy new data to final focuses table
INSERT="INSERT INTO public.$OUTPUT_TABLE(geom,classname, view_date, sensor, areamunkm) "
INSERT=$INSERT"SELECT geometries as geom, classname, view_date, sensor, areamunkm FROM $TARGET "
# drop the intermediary table
DROP_MONTH_TABLE="DROP TABLE $TARGET"
# control of end
CTRL_ALERTS_CERRADO=false
# exec process
. ./import_data.sh