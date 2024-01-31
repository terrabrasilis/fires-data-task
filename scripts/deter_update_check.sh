#!/bin/bash
# Check that the DETER data from the previous month is complete

JSON_RESPONSE=$(curl -s "$GEOSERVER_BASE_URL/$GEOSERVER_BASE_PATH/$PROJECT_NAME/wfs?SERVICE=WFS&REQUEST=GetFeature&VERSION=2.0.0&TYPENAME=$LAYER_NAME&OUTPUTFORMAT=application%2Fjson")
DETER_LAST_DATE=$(echo $JSON_RESPONSE |grep -oP '(?<="updated_date":")[^"]*')
if [[ $DETER_LAST_DATE =~ ^[0-9]{4}-[0-9]{2}-[0-9]{2}$ ]] && date -d "$DETER_LAST_DATE" >/dev/null 2>&1 ;
then
  DETER_LAST_DATE=$(date +%s -d $DETER_LAST_DATE)
else
  echo "Invalid GeoServer response to $PROJECT_NAME"
  exit
fi;

# is the last date of the DETER data greater than or equal to the first day of the current month?
if [ "$DETER_LAST_DATE" -ge "$CURRENT_MONTH" ]; then
  echo "DETER last month is complete to $PROJECT_NAME"
  echo "Next steps to load and proccess data"
  export CURRENT_MONTH
  # echo "$CURRENT_MONTH" > "$DATA_DIR/processed-month-control"
else
  echo "DETER last month is incomplete to $PROJECT_NAME"
  # comment out the output command to continue even when data is incomplete
  exit
fi;