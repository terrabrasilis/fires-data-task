#!/bin/bash
#
# get first day of current month
YEAR=$(date +%Y)
MONTH=$(date +%m)
CURRENT_MONTH="$YEAR-$MONTH-01"
CURRENT_MONTH=$(date +%s -d $CURRENT_MONTH)

# if the control file exists, load the date of the last process performed.
if [[ -f "$DATA_DIR/processed-month-control" ]]; then
  PROCESSED_MONTH=$(cat $DATA_DIR/processed-month-control)
  if [[ "$PROCESSED_MONTH" -eq "$CURRENT_MONTH" ]]; then
    echo "Skip the process. There is no new data."
    exit
  fi
fi

GEOSERVER_BASE_URL="http://terrabrasilis.dpi.inpe.br"
GEOSERVER_BASE_PATH="geoserver"
LAYER_NAME="last_date"

PROJECT_NAME="deter-amz"
# check to AMZ
. ./deter_update_check.sh

PROJECT_NAME="deter-cerrado-nb"
# check to CERRADO
. ./deter_update_check.sh