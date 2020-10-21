#!/bin/bash
. ./dbconf.sh

MONTH_TABLE="focuses"
FOCUSES_TABLE="focos_aqua_referencia"

PG_BIN="/usr/bin"
PG_CON="-d $database -p $port -U $user -h $host"
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
LOGFILE="$DATA_DIR/import_focuses_$DATE_LOG.log"

# set a default value to numberMatched to skip process if no control file exists.
numberMatched=0
# verify if has new focuses
if [[ -f "$DATA_DIR/acquisition_data_control" ]];
then
  source "$DATA_DIR/acquisition_data_control"
  INSERT_INFOS="INSERT INTO public.acquisition_data_control(focus_start_date, focus_end_date, num_focuses) "
  INSERT_INFOS=$INSERT_INFOS"VALUES ('$START_DATE', '$END_DATE', $numberMatched);"
  CHECK_DATA="SELECT num_focuses FROM public.acquisition_data_control WHERE focus_start_date='$START_DATE' AND focus_end_date='$END_DATE'"
else
  echo "No have data" >> $LOGFILE
  exit
fi

# obtain the number of focuses from the previous import process, if any
NUM_FOCUSES=($($PG_BIN/psql $PG_CON -t -c "$CHECK_DATA"))

if [[ "$numberMatched" = "$NUM_FOCUSES" ]];
then
  echo "The data was imported before" >> $LOGFILE
  echo "If you want to import again, follow these steps:" >> $LOGFILE
  echo " - Verify if your table, $FOCUSES_TABLE, do not have these data;" >> $LOGFILE
  echo " - Verify if the control table, acquisition_data_control, do not have these control data;" >> $LOGFILE
  echo " - Remove the control file, acquisition_data_control;" >> $LOGFILE
  echo "" >> $LOGFILE
  echo "The previous data on the control record are:" >> $LOGFILE
  echo "START_DATE=$START_DATE, END_DATE=$END_DATE, numberMatched=$numberMatched" >> $LOGFILE
  exit
else
  echo "The data will now be imported" >> $LOGFILE

  # to control the import shape mode
  CREATE_TABLE="YES"
  for ZIP_FILE in `ls $DATA_DIR/*.zip | awk {'print $1'}`
  do
    FILE_NAME=`basename $ZIP_FILE`

    unzip -o -j "$ZIP_FILE" -d "$DATA_DIR"

    for SHP_NAME in `ls $DATA_DIR/*.shp | awk {'print $1'}`
    do
      SHP_NAME=`basename $SHP_NAME`
      SHP_NAME=`echo $SHP_NAME | cut -d "." -f 1`

      PROJ4=`gdalsrsinfo -o proj4 $DATA_DIR/$SHP_NAME.shp`
      # find the EPSG code to reproject
      SQL="SELECT srid FROM public.spatial_ref_sys WHERE proj4text = $PROJ4"
      EPSG=($($PG_BIN/psql $PG_CON -t -c "$SQL"))

      # If table exists change command to append mode
      if [[ "$CREATE_TABLE" = "YES" ]]; then
          SHP2PGSQL_OPTIONS="-c -s $EPSG:4326 -W 'LATIN1' -g geometries"
          CREATE_TABLE="NO"
      else
          SHP2PGSQL_OPTIONS="-a -s $EPSG:4326 -W 'LATIN1' -g geometries"
      fi

      # import shapefiles
      if $PG_BIN/shp2pgsql $SHP2PGSQL_OPTIONS $DATA_DIR/$SHP_NAME $MONTH_TABLE | $PG_BIN/psql $PG_CON
      then
          echo "Import ($FILE_NAME) ... OK" >> $LOGFILE
          rm $DATA_DIR/$SHP_NAME.{dbf,prj,shp,shx,cst}
          rm $DATA_DIR/"wfsrequest.txt"
      else
          echo "Import ($FILE_NAME) ... FAIL" >> $LOGFILE
          exit
      fi
    done
  done
  # If the execution arrives here, all the data has been imported. 
  $PG_BIN/psql $PG_CON -t -c "$INSERT_INFOS"
  rm "$DATA_DIR/acquisition_data_control"

  # copy new data to final focuses table
  INSERT="INSERT INTO public.$FOCUSES_TABLE(geom, datahora, satelite, pais, estado, municipio, bioma, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data) "
  INSERT=$INSERT"SELECT geometries as geom, data_hora_::text as datahora, satelite, pais, estado, municipio, bioma, numero_dia as diasemchuva, precipitac as precipitacao, risco_fogo as riscofogo, latitude, longitude, frp, data_hora_::date as data FROM $MONTH_TABLE "
  $PG_BIN/psql $PG_CON -t -c "$INSERT"

  DROP_MONTH_TABLE="DROP TABLE $MONTH_TABLE"
  $PG_BIN/psql $PG_CON -t -c "$DROP_MONTH_TABLE"
fi