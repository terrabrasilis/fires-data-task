#!/bin/bash
if [[ -f "$DATA_DIR/config/pgconfig" ]];
then
  source "$DATA_DIR/config/pgconfig"
  PGCONNECTION="host=$host port=$port dbname='$dbname' user='$user' password='$password'"
else
  echo "Missing Postgres config file."
  exit
fi