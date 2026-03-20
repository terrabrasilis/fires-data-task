#!/bin/bash
#
# ONLY to debug in localhost
## SCRIPT_DIR=`pwd`
## SHARED_DIR=$SCRIPT_DIR"/../data"
## DETER_VIEW_DATE="2023-08-01"

# The data work directory.
export DATA_DIR=${SHARED_DIR}

# go to the scripts directory
cd ${SCRIPT_DIR}

echo "#############################################"
echo "# Starting copy DETER and Active Fires data"
echo "# $(date +"%Y-%m-%d %H:%M:%S")"
echo "#############################################"
# update focuses and alerts
python3 python/copy_data.py

echo "#############################################"
echo "# Starting rasterize process with GDAL"
echo "# $(date +"%Y-%m-%d %H:%M:%S")"
echo "#############################################"
# load postgres parameters from config file in config/pgconfig
. ./dbconf.sh
. ./gdal_process.sh

echo "#############################################"
echo "# Starting classify - Active Fires x PRODES"
echo "# $(date +"%Y-%m-%d %H:%M:%S")"
echo "#############################################"
# update focuses classification
export DATA_TYPE="prodes"
python3 python/classify_data.py

echo "#############################################"
echo "# Starting classify - Active Fires x CAR"
echo "# $(date +"%Y-%m-%d %H:%M:%S")"
echo "#############################################"

export DATA_TYPE="car"
python3 python/classify_data.py

echo "#############################################"
echo "# The end"
echo "# $(date +"%Y-%m-%d %H:%M:%S")"
echo "#############################################"