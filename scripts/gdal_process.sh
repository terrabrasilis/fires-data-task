#!/bin/bash
#
# This script is used to produce one Geotiff file with PRODES + DETER data
# Its file is used by Active Fires classify process to Fires Dashboard
OUTPUT_FILE="fires_dashboard_prodes"

# some usefull configurations for GDAL
export CHECK_DISK_FREE_SPACE=NO
export GDAL_CACHEMAX=10%
export GDAL_NUM_THREADS=ALL_CPUS

# default values for BBOX and Pixel size.
# force the same BBOX Brazil
BBOX="-73.98318215899995 -33.75117799399993 -28.847770352999916 5.269580833000035"
PIXEL_SIZE="0.000268900 -0.000268900"

# got to de work directory
cd $DATA_DIR"/"
# remove old output file
if [[ -f ${OUTPUT_FILE}".tif" ]]; then
    rm ${OUTPUT_FILE}".tif"
fi;

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

DT=$(date +"%Y-%m-%d_%H:%M:%S")
echo "Start rasterize for DETER: ${DT}"
# DETER - source vector data
SQL="SELECT geom FROM public.deter WHERE view_date >= '$DETER_VIEW_DATE';"

gdal_rasterize -burn ${pv_rd} -tr ${PIXEL_SIZE} -te ${BBOX} \
-co "COMPRESS=LZW" -co "BIGTIFF=YES" \
-a_nodata 0 -ot Byte PG:"$PGCONNECTION" \
-sql "${SQL}" "deter_since_${DETER_VIEW_DATE}_pv${pv_rd}.tif"

# ###############################################################
# Merge DETER and the last 3 years of PRODES
# ###############################################################

# remove old DETER + PRODES Geotiff
if [[ -f "fires_dashboard_deter_prodes_p3.tif" ]]; then
    rm fires_dashboard_deter_prodes_p3.tif
fi;

DT=$(date +"%Y-%m-%d_%H:%M:%S")
echo "Start merge for PRODES+DETER: ${DT}"
# merge
gdalbuildvrt fires_dashboard_deter_prodes.vrt "${PRODES_P3}" "deter_since_${DETER_VIEW_DATE}_pv${pv_rd}.tif"
gdal_translate -of GTiff -co "COMPRESS=LZW" -co "BIGTIFF=YES" fires_dashboard_deter_prodes.vrt fires_dashboard_deter_prodes.tif

DT=$(date +"%Y-%m-%d_%H:%M:%S")
echo "Start proximity build for PRODES+DETER: ${DT}"
# build proximity map
gdal_proximity.py -co "COMPRESS=LZW" -co "BIGTIFF=YES" \
fires_dashboard_deter_prodes.tif fires_dashboard_deter_prodes_dist.tif \
-values ${pv_rd} -nodata 0 -ot Byte

DT=$(date +"%Y-%m-%d_%H:%M:%S")
echo "Start buffer calc for PRODES+DETER: ${DT}"
# buffer calc
gdal_calc.py --co="COMPRESS=LZW" --co="BIGTIFF=YES" --NoDataValue=0 \
-A fires_dashboard_deter_prodes_dist.tif --type=Byte --quiet \
--calc="((A<=0)*${pv_rd} + ${pv_rdb}*logical_and(A>=1,A<=17))" \
--outfile="fires_dashboard_deter_prodes_p3.tif"


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

    DT=$(date +"%Y-%m-%d_%H:%M:%S")
    echo "Start proximity build for OLD PRODES: ${DT}"
    # build proximity map
    gdal_proximity.py -co "COMPRESS=LZW" -co "BIGTIFF=YES" \
    ${PRODES_P2} fires_dashboard_prodes_p2_dist.tif -values ${pv_cd} -nodata 0 -ot Byte

    DT=$(date +"%Y-%m-%d_%H:%M:%S")
    echo "Start buffer calc for OLD PRODES: ${DT}"
    # buffer calc
    gdal_calc.py --co="COMPRESS=LZW" --co="BIGTIFF=YES" --NoDataValue=0 \
    -A "fires_dashboard_prodes_p2_dist.tif" --type=Byte --quiet \
    --calc="((A<=0)*${pv_cd} + ${pv_cdb}*logical_and(A>=1,A<=17))" \
    --outfile="fires_dashboard_prodes_buffer_p2.tif"

    # remove intermediary file
    
    if [[ -f "fires_dashboard_prodes_p2_dist.tif" ]]; then
        rm fires_dashboard_prodes_p2_dist.tif
    fi;

    # store new md5sum to use in next time
    echo "${P2_MD5_CHECK}" > "${PRODES_P2}.md5"
fi;

# ###############################################################
# Build the final file
# ###############################################################

DT=$(date +"%Y-%m-%d_%H:%M:%S")
echo "Start merge the three parts: ${DT}"
# merge prodes base file + prodes old supression + prodes/deter recent supression
gdalbuildvrt ${OUTPUT_FILE}".vrt" ${PRODES_P1} \
fires_dashboard_prodes_buffer_p2.tif fires_dashboard_deter_prodes_p3.tif
gdal_translate -of GTiff -co "COMPRESS=LZW" -co "BIGTIFF=YES" ${OUTPUT_FILE}".vrt" ${OUTPUT_FILE}".tif"

# ###############################################################
# Remove intermediary files to release disk space
# ###############################################################

if [[ -f "fires_dashboard_deter_prodes.tif" ]]; then
    rm fires_dashboard_deter_prodes.tif
fi;
if [[ -f "deter_since_"${DETER_VIEW_DATE}"_pv${pv_rd}.tif" ]]; then
    rm deter_since_"${DETER_VIEW_DATE}"_pv${pv_rd}.tif
fi;
if [[ -f "fires_dashboard_deter_prodes_dist.tif" ]]; then
    rm fires_dashboard_deter_prodes_dist.tif
fi;

# return to the old path
cd -