#!/bin/bash
#
# ONLY to debug in localhost
## SCRIPT_DIR=`pwd`
## SHARED_DIR=$SCRIPT_DIR"/../data"
## DETER_VIEW_DATE="2023-08-01"

# to store run log
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
# The data work directory.
export DATA_DIR=${SHARED_DIR}

# go to the scripts directory
cd $SCRIPT_DIR

echo "#############################################"
echo "# Starting copy DETER and Active Fires data"
echo "# ${DATE_LOG}"
echo "#############################################"
# update focuses and alerts
python3 python/copy_data.py

echo "#############################################"
echo "# Starting rasterize process with GDAL"
echo "# ${DATE_LOG}"
echo "#############################################"
# load postgres parameters from config file in config/pgconfig
. ./dbconf.sh
. ./gdal_process.sh >> "$DATA_DIR/gdal_process_$DATE_LOG.log" 2>&1

echo "#############################################"
echo "# Starting classify - Active Fires x PRODES"
echo "# ${DATE_LOG}"
echo "#############################################"
# update focuses classification
export DATA_TYPE="prodes"
python3 python/classify_data.py

echo "#############################################"
echo "# Starting classify - Active Fires x CAR"
echo "# ${DATE_LOG}"
echo "#############################################"

export DATA_TYPE="car"
python3 python/classify_data.py

echo "#############################################"
echo "# The end"
echo "# ${DATE_LOG}"
echo "#############################################"