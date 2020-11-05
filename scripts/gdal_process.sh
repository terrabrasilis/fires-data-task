#!/bin/bash
OUTPUT_TABLE=$deteroutputtable
SQL="SELECT geom FROM "$OUTPUT_TABLE" WHERE view_date >= '$DETER_VIEW_DATE' "
SQL=$SQL"and classname in ('DESMATAMENTO_VEG','DESMATAMENTO_CR','MINERACAO')"
PGCONNECTION="host=$host port=$port dbname=$database user=$user password=$PGPASSWORD"

cd $DATA_DIR"/"

# 2.3) from step-to-step
gdal_rasterize -burn 15 -tr 0.000268999526293 -0.000269000921852 \
-te -73.9783164 -18.0406670 -43.9135844 5.2714909 \
-co "COMPRESS=LZW" \
-a_nodata 0 -ot Byte PG:"$PGCONNECTION" \
-sql "$SQL" "deter_since_"$DETER_VIEW_DATE"_pv15.tif"

# 2.4) from step-to-step
gdalbuildvrt prodes_deter_desmate_recente_pv15.vrt prodes_desmate_recente_pv15.tif "deter_since_"$DETER_VIEW_DATE"_pv15.tif"
gdal_translate prodes_deter_desmate_recente_pv15.vrt  prodes_deter_desmate_recente_pv15.tif

# 3.1) from step-to-step (gdal3 is needed)
gdal_proximity.py prodes_deter_desmate_recente_pv15.tif prodes_deter_desmate_recente_pv15_dist.tif -values 15 -nodata 0 -ot Byte

# 3.3) from step-to-step
gdal_calc.py -A prodes_deter_desmate_recente_pv15_dist.tif --calc="(15*logical_and(A>=0,A<=17))" --NoDataValue=0 --outfile prodes_deter_desmate_recente_pv15_dist_fat.tif

# 3.4) from step-to-step
gdalbuildvrt prodes_agregado.vrt  prodes_floresta_pv1.tif  prodes_desmate_consolidado_pv10_dist_fat.tif prodes_deter_desmate_recente_pv15_dist_fat.tif
gdal_translate prodes_agregado.vrt  prodes_agregado.tif

# 4) from step-to-step
python3 $SCRIPT_DIR"/get-class.py" -H $host -P $port -d $database -u $user -p $password -t prodes -D "$DATA_DIR"
python3 $SCRIPT_DIR"/get-class.py" -H $host -P $port -d $database -u $user -p $password -t car -D "$DATA_DIR"