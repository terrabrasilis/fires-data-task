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
  if [ "$PROCESSED_MONTH" -eq "$CURRENT_MONTH" ]; then
    echo "Skip the process. There is no new data."
    exit
  fi
fi

GEOSERVER_BASE_URL="http://terrabrasilis.dpi.inpe.br"
GEOSERVER_BASE_PATH="geoserver"
PROJECT_NAME="deter-amz"
LAYER_NAME="last_date"
JSON_RESPONSE=$(curl -s "$GEOSERVER_BASE_URL/$GEOSERVER_BASE_PATH/$PROJECT_NAME/wfs?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&TYPENAME=$LAYER_NAME&OUTPUTFORMAT=application%2Fjson")
DETER_LAST_DATE=$(echo $JSON_RESPONSE |grep -oP '(?<="updated_date":")[^"]*')

if [[ $DETER_LAST_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && date -d "$DETER_LAST_DATE" >/dev/null 2>&1 ;
then
  DETER_LAST_DATE=$(date +%s -d $DETER_LAST_DATE)

  # is the last date of the DETER data greater than or equal to the first day of the current month?
  if [ "$DETER_LAST_DATE" -ge "$CURRENT_MONTH" ]; then
    echo "DETER last month is complete"
    echo "Next steps to load and proccess data"
    export CURRENT_MONTH
    # echo "$CURRENT_MONTH" > "$DATA_DIR/processed-month-control"
  else
    echo "DETER last month is incomplete"
    exit
  fi
fi;