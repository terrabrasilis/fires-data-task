#!/bin/bash
#
# This script is used to produce one Geotiff file with PRODES + DETER data
# Its file is used by Active Fires classify process to Fires Dashboard
OUTPUT_FILE="prodes_agregado.tif"

# got to de work directory
cd $DATA_DIR"/"
# remove old output file
rm ${OUTPUT_FILE}


# ###############################################################
# PRODES products - input files
# ###############################################################
#   p1 = product 1 - prodes base file (forest + no-forest + hydrography)
#   p2 = product 2 - consolidate deforestation 
#   p3 = product 3 - recent deforestation
PRODES_P1="fires_dashboard_prodes_p1.tif"
PRODES_P2="fires_dashboard_prodes_p2.tif"
PRODES_P3="fires_dashboard_prodes_p3.tif"

# ###############################################################
# Prepare DETER data from last year PRODES
# ###############################################################
#   pixel value
#   15 = recent deforestation
#   16 = recent deforestation buffer
pv_rd=15
pv_rdb=16

# DETER - vector to raster
SQL="SELECT geom FROM public.deter WHERE view_date >= '$DETER_VIEW_DATE';"

gdal_rasterize -burn ${pv_rd} -tr 0.0002657497628524051257 -0.0002657504795300113837 \
-te -73.9831821589999521 -33.7473232569939228 -28.8479766863846123 5.2714908999999999 \
-co "COMPRESS=LZW" \
-a_nodata 0 -ot Byte PG:"$PGCONNECTION" \
-sql "$SQL" "deter_since_${DETER_VIEW_DATE}_pv${pv_rd}.tif"

# ###############################################################
# Merge DETER and the last 3 years of PRODES
# ###############################################################

# remove old DETER + PRODES Geotiff
rm fires_dashboard_deter_prodes_p3.tif

# merge
gdalbuildvrt fires_dashboard_deter_prodes.vrt ${PRODES_P3} "deter_since_${DETER_VIEW_DATE}_pv${pv_rd}.tif"
gdal_translate -of GTiff -co "COMPRESS=LZW" -co BIGTIFF=YES fires_dashboard_deter_prodes.vrt fires_dashboard_deter_prodes.tif

# build proximity map
gdal_proximity.py -co "COMPRESS=LZW" -co "BIGTIFF=YES" \
fires_dashboard_deter_prodes.tif fires_dashboard_deter_prodes_dist.tif -values ${pv_rd} -nodata 0 -ot Byte

# buffer calc
gdal_calc.py --co="COMPRESS=LZW" --co="BIGTIFF=YES" --NoDataValue=0 \
-A fires_dashboard_deter_prodes_dist.tif --type=Byte --quiet \
--calc="((A<=0)*${pv_rd} + ${pv_rdb}*logical_and(A>=1,A<=17))" \
--outfile fires_dashboard_deter_prodes_p3.tif

# ###############################################################
# Apply buffer into PRODES consolidate deforestation
# ###############################################################

# If prodes buffer file exists and the md5sum of original input do not change, avoid rebuild the buffer.
P2_MD5=""
P2_MD5_CHECK=""
# if p2 input file exists, do md5 sum
if [[ -f "${PRODES_P2}" ]];
then
    P2_MD5_CHECK=$(md5sum "${PRODES_P2}" |cut -d' ' -f1)
fi;

# if buffer file and md5 file exists, read the old md5 sum
if [[ -f "fires_dashboard_prodes_buffer_p2.tif" && -f "${PRODES_P2}.md5" ]];
then
    P2_MD5=$(cat "${PRODES_P2}.md5")
fi;

# when p2 input file changes, then we rebuild the buffer over p2
if [[ ! "${P2_MD5_CHECK}" = "" && ! "${P2_MD5}" = "${P2_MD5_CHECK}" ]];
then
    #   pixel value
    #   10 = consolidate deforestation
    #   11 = consolidate deforestation buffer
    pv_cd=10
    pv_cdb=11

    # build proximity map
    gdal_proximity.py -co "COMPRESS=LZW" -co "BIGTIFF=YES" \
    ${PRODES_P2} fires_dashboard_prodes_p2_dist.tif -values ${pv_cd} -nodata 0 -ot Byte

    # buffer calc
    gdal_calc.py --co="COMPRESS=LZW" --co="BIGTIFF=YES" --NoDataValue=0 \
    -A "fires_dashboard_prodes_p2_dist.tif" --type=Byte --quiet \
    --calc="((A<=0)*${pv_cd} + ${pv_cdb}*logical_and(A>=1,A<=17))" \
    --outfile="fires_dashboard_prodes_buffer_p2.tif"

    # remove intermediary file
    rm fires_dashboard_prodes_p2_dist.tif

    # store new md5sum to use in next time
    echo "${P2_MD5_CHECK}" > "${PRODES_P2}.md5"
fi;

# ###############################################################
# Merge DETER + PRODES
# ###############################################################

# merge prodes base file + prodes old supression + prodes/deter recent supression
gdalbuildvrt prodes_agregado.vrt ${PRODES_P1} \
fires_dashboard_prodes_buffer_p2.tif fires_dashboard_deter_prodes_p3.tif
gdal_translate -of GTiff -co "COMPRESS=LZW" -co BIGTIFF=YES prodes_agregado.vrt ${OUTPUT_FILE}

# ###############################################################
# Remove intermediary files to release disk space
# ###############################################################

rm fires_dashboard_deter_prodes.tif
rm deter_since_"${DETER_VIEW_DATE}"_pv${pv_rd}.tif
rm fires_dashboard_deter_prodes_dist.tif

# return to the old path
cd -