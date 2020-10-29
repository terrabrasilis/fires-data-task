#!/bin/bash
# The view date reference of DETER used to deter_rasterize in the SQL filter. (view_date >= '2019-08-01')
DETER_VIEW_DATE="2019-08-01"
# The script work directory.
DATA_DIR=`pwd`
DATA_DIR=$DATA_DIR"/../data"
export DATA_DIR
# get focuses and alerts for last month
python3 download-month-data.py

. ./import_focuses.sh

. ./import_alerts.sh

. ./gdal_process.sh