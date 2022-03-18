#!/bin/bash
OUTPUT_TABLE=$deteroutputtable
SQL="SELECT geom FROM "$OUTPUT_TABLE" WHERE view_date >= '$DETER_VIEW_DATE' "
SQL=$SQL"and classname in ('DESMATAMENTO_VEG','DESMATAMENTO_CR','MINERACAO')"
PGCONNECTION="host=$host port=$port dbname=$database user=$user password=$PGPASSWORD"

cd $DATA_DIR"/"

# 2.3) from step-to-step
gdal_rasterize -burn 15 -tr 0.000268999526293 -0.000269000921852 \
-te -73.9783164 -24.6847207 -41.5219096 5.2714909 \
-co "COMPRESS=LZW" \
-a_nodata 0 -ot Byte PG:"$PGCONNECTION" \
-sql "$SQL" "deter_since_${DETER_VIEW_DATE}_pv15.tif"

# 3.1) from step-to-step (gdal3 is needed) changed 30/08/2021
gdal_proximity.py "deter_since_${DETER_VIEW_DATE}_pv15.tif" "deter_since_${DETER_VIEW_DATE}_pv15_dist.tif" -values 15 -nodata 0 -ot Byte

# 3.3) from step-to-step
gdal_calc.py -A "deter_since_${DETER_VIEW_DATE}_pv15_dist.tif" --calc="(15*logical_and(A>=0,A<=17))" --NoDataValue=0 --outfile "deter_since_${DETER_VIEW_DATE}_pv15_dist_fat.tif"

# 2.4) from step-to-step
gdalbuildvrt prodes_agregado.vrt prodes_agregado_vseg_amz_cerrado.tif "deter_since_${DETER_VIEW_DATE}_pv15_dist_fat.tif"
gdal_translate -of GTiff -co "COMPRESS=LZW" -co BIGTIFF=YES prodes_agregado.vrt prodes_agregado.tif

# rename DETER's aggregate deforestation, compress and send to download area
mv "deter_since_${DETER_VIEW_DATE}_pv15_dist_fat.tif" deter_agregado_amz_cerrado.tif
zip -j deter_agregado_amz_cerrado.zip deter_agregado_amz_cerrado.tif deter_agregado_amz_cerrado.qml
mv deter_agregado_amz_cerrado.zip "${DOWNLOAD_AREA}/"

# remove intermediary data
rm deter_since_"${DETER_VIEW_DATE}"_pv15*
rm deter_agregado_amz_cerrado.tif

# 4) from step-to-step
python3 $SCRIPT_DIR"/get-class.py" -H $host -P $port -d $database -u $user -p $password -t prodes -D "$DATA_DIR"
python3 $SCRIPT_DIR"/get-class.py" -H $host -P $port -d $database -u $user -p $password -t car -D "$DATA_DIR"

if $CTRL_ALERTS_AMZ && $CTRL_ALERTS_CERRADO && $CTRL_FOCUSES;
then
  echo "$CURRENT_MONTH" > "$DATA_DIR/processed-month-control"
fi