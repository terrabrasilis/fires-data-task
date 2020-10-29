#!/bin/bash
if [[ -f "$DATA_DIR/config/pgconfig" ]];
then
  source "$DATA_DIR/config/pgconfig"
  export PGUSER=$user
  export PGPASSWORD=$password
  PG_BIN="/usr/bin"
  PG_CON="-d $database -p $port -U $user -h $host"
else
  echo "Missing Postgres config file."
  exit
fi