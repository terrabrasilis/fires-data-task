# To build image for this dockerfile use this command:
#   docker build -t terrabrasilis/fires-data-task:vx.y -f env-scripts/Dockerfile --no-cache .
#
# To run without compose and without shell terminal use this command:
#   docker run -d --rm --name terrabrasilis_fires_scripts terrabrasilis/fires-data-task:vx.y
#   docker run -d --rm --name terrabrasilis_fires_scripts -v $PWD:/logs -v $PWD:/data/files terrabrasilis/fires-data-task:vx.y
#
#--------- Generic stuff all our Dockerfiles should start with so we get caching ------------
FROM osgeo/gdal:ubuntu-small-3.2.0

LABEL "br.inpe.dpi"="INPE/DPI-TerraBrasilis" \
br.inpe.dpi.terrabrasilis="script-tasks" \
author="Andre Carvalho" \
author.email="andre.carvalho@inpe.br" \
description="Scripts for data preparation of fire focuses."
#-------------Application Specific Stuff ----------------------------------------------------

RUN apt-get -o Acquire::ForceIPv4=true update \
    && apt-get install -y \
    cron \
    python3-pip \
    postgis \
    zip \
    && rm -rf /var/lib/apt/lists/*

# define the timezone to run cron
ENV TZ=America/Sao_Paulo
# define the install path env var
ENV INSTALL_PATH /usr/local
# the data directory for put generated files 
ENV SHARED_DIR $INSTALL_PATH/data
# the common download area
ENV DOWNLOAD_AREA $INSTALL_PATH/download
# the scripts directory
ENV SCRIPT_DIR $INSTALL_PATH/scripts-shell

# create directories
RUN mkdir -p ${SHARED_DIR} \
    && mkdir -p ${SCRIPT_DIR} \
    && mkdir -p ${SHARED_DIR}/logs \
    && touch ${SHARED_DIR}/logs/exec_monthly.log

# INSTALL SCRIPTS
# ------------------------------------------------------
COPY scripts/ $SCRIPT_DIR/
ADD env-scripts/exec_monthly.sh $INSTALL_PATH/
ADD env-scripts/monthly.cron /etc/cron.d/monthly-cron
ADD env-scripts/docker-entrypoint.sh $INSTALL_PATH/bin/docker-entrypoint.sh
ADD env-scripts/requirements.txt $INSTALL_PATH/

RUN pip3 install -r $INSTALL_PATH/requirements.txt \
    && chmod +x $SCRIPT_DIR/*.sh \
    && chmod +x $INSTALL_PATH/*.sh \
    && chmod 0644 /etc/cron.d/monthly-cron \
    && crontab -l | { cat; cat /etc/cron.d/monthly-cron; } | crontab - \
    && chmod +x $INSTALL_PATH/bin/*.sh \
    && ln -s usr/local/bin/docker-entrypoint.sh / # backwards compat

# expose shared dir
VOLUME ["${SHARED_DIR}", "${DOWNLOAD_AREA}"]

ENTRYPOINT [ "/docker-entrypoint.sh" ]