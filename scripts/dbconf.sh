#!/bin/bash

if [[ -f "$DATA_DIR/config/pgconfig" ]];
then
  source "$DATA_DIR/config/pgconfig"
  export PGUSER=$user
  export PGPASSWORD=$pass
else
  echo "Missing Postgres config file."
  exit
fi