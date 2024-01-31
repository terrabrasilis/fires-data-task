#!/bin/bash
# copy focuses from raw_fires_data database using a SQL View. See the README.md
TARGET="focuses"
OUTPUT_TABLE=$firesoutputtable

# define de target directory
DATA_TARGET="$DATA_DIR/$TARGET"
# define log file
DATE_LOG=$(date +"%Y-%m-%d_%H:%M:%S")
LOGFILE="$DATA_TARGET/copy_focuses_$DATE_LOG.log"

# verify if control file exists
if [[ -f "$DATA_TARGET/acquisition_data_control" ]];
then
    # We read START_DATE and END_DATE from the "acquisition_data_control" file.
    # These values are set by the __getPreviousMonthRangeDate function in download-month-data.py
    # because it has been used in the past to download focus data. After disabling the download, in favor of "general-fires-data-task",
    # this behavior was maintained.
    source "$DATA_TARGET/acquisition_data_control"

    CREATE_TABLE="CREATE TABLE ${TARGET} as"
    CREATE_TABLE="${CREATE_TABLE} SELECT geom, datahora, satelite, pais, estado, municipio, bioma,"
    CREATE_TABLE="${CREATE_TABLE} diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data"
    CREATE_TABLE="${CREATE_TABLE} FROM public.raw_fires_data_online"
    CREATE_TABLE="${CREATE_TABLE} WHERE data BETWEEN '${START_DATE}'::date AND '${END_DATE}'::date;"
    $PG_BIN/psql $PG_CON -t -c "$CREATE_TABLE"

    CREATE_INDEX="CREATE INDEX ${TARGET}_geom_idx ON public.${TARGET} USING gist (geom);"
    $PG_BIN/psql $PG_CON -t -c "$CREATE_INDEX"

    COUNT="SELECT COUNT(*) FROM public.${TARGET};"
    # obtain the number of rows from the temporary table
    numberMatched=($($PG_BIN/psql $PG_CON -t -c "$COUNT"))

    CHECK_DATA="SELECT num_rows FROM public.acquisition_data_control WHERE start_date='$START_DATE' AND end_date='$END_DATE' AND origin_data='$TARGET' ORDER BY id DESC LIMIT 1"
    # obtain the number of rows from the previous import process, if any
    NUM_ROWS=($($PG_BIN/psql $PG_CON -t -c "$CHECK_DATA"))
    if [[ "$numberMatched" = "$NUM_ROWS" ]];
    then
        echo "Canceled because focus data was imported earlier."
    else
        UPDATE_BIOME="UPDATE public.focuses SET bioma=b.legend"
        UPDATE_BIOME="${UPDATE_BIOME} FROM public.biome b WHERE ST_Intersects(public.focuses.geom, b.geom);"
        $PG_BIN/psql $PG_CON -t -c "$UPDATE_BIOME"

        # copy new data to final focuses table
        INSERT="INSERT INTO public.$OUTPUT_TABLE(geom, datahora, satelite, pais, estado, municipio, bioma, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data) "
        INSERT="${INSERT} SELECT geom, datahora, satelite, pais, estado, municipio, bioma, diasemchuva, precipitacao, riscofogo, latitude, longitude, frp, data FROM $TARGET "
        $PG_BIN/psql $PG_CON -t -c "$INSERT"

        INSERT_INFOS="INSERT INTO public.acquisition_data_control(start_date, end_date, num_rows, origin_data) "
        INSERT_INFOS=$INSERT_INFOS"VALUES ('$START_DATE', '$END_DATE', $numberMatched,'$TARGET');"
        $PG_BIN/psql $PG_CON -t -c "$INSERT_INFOS"

        export CTRL_FOCUSES=true
    fi;

    # drop the intermediary month table
    DROP_MONTH_TABLE="DROP TABLE IF EXISTS $TARGET"
    $PG_BIN/psql $PG_CON -t -c "$DROP_MONTH_TABLE"

    rm "$DATA_TARGET/acquisition_data_control"
fi;