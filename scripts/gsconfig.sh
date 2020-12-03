#!/bin/bash
if [[ -f "$DATA_DIR/config/gsconfig" ]];
then
  source "$DATA_DIR/config/gsconfig"
  export FOCUSES_USER=$FOCUSES_USER
  export FOCUSES_PASS=$FOCUSES_PASS
  export ALERTS_USER=$ALERTS_USER
  export ALERTS_PASS=$ALERTS_PASS
else
  echo "Missing GeoServer config file."
  echo "Proceed without username and password."
fi