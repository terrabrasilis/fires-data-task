"""
Download via WFS
Download Shapefile Focuses
Download Shapefile DETER alerts

Copyright 2020 TerraBrasilis

Usage:
  download-month-data.py

Options:
  no have

Notes about code.

This is based on the DETER data download example provided in the following link.
https://gist.github.com/andre-carvalho/45eaf4378fbf91d0514a995a80c69d98
"""

import requests, os, io
from requests.auth import HTTPBasicAuth
from datetime import datetime
from calendar import monthrange
from xml.etree import ElementTree as xmlTree

class DownloadWFS:
  """
    Define configurations on instantiate.

    First parameter: user, The user name used to authentication on the server.

    Second parameter: password, The password value used to authentication on the server.
    
    To change the predefined settings, inside the constructor, edit the
    parameter values ​​in accordance with the respective notes.
    """

  def __init__(self):
    """
    Constructor with predefined settings.

    The start date and end date are automatically detected using the machine's calendar
    and represent the first and last day of the past month.

    Important note: If the range used to filter is very wide, the number of resources
    returned may be greater than the maximum limit allowed by the server.
    In this case, this version has been prepared for pagination and the shapefile is
    downloaded in parts.
    """
    self.START_DATE,self.END_DATE=self.__getLastMonthRangeDate()
    # Data directory for writing downloaded data
    self.DIR=os.path.realpath(os.path.dirname(__file__))
    self.DIR=os.getenv("DATA_DIR", self.DIR)

  def __configForTarget(self):
    # define the base directory to store downloaded data
    self.DATA_DIR="{0}/{1}".format(self.DIR,self.TARGET)
    os.makedirs(self.DATA_DIR, exist_ok=True) # create the output directory if it not exists

    self.AUTH=None
    user=None
    password=None

    if self.TARGET=="focuses":
      self.WORKSPACE_NAME="terrabrasilis"
      self.LAYER_NAME="focos"
      self.serverLimitByTarget=10000
      user=os.getenv("FOCUSES_USER", user)
      password=os.getenv("FOCUSES_PASS", password)
      if user and password:
        self.AUTH=HTTPBasicAuth(user, password)
    else:
      self.WORKSPACE_NAME="deter-amz"
      self.LAYER_NAME="deter_amz_auth"
      self.serverLimitByTarget=100000
      user=os.getenv("ALERTS_USER", user)
      password=os.getenv("ALERTS_PASS", password)
      if user and password:
        self.AUTH=HTTPBasicAuth(user, password)

    # The output file name (layer_name_start_date_end_date)
    self.OUTPUT_FILENAME="{0}_{1}_{2}".format(self.LAYER_NAME,self.START_DATE,self.END_DATE)

  def __getLastMonthRangeDate(self):
    """
    The start date and end date are automatically detected using the machine's calendar
    and represent the first and last day of the past month.
    """
    last_month=(datetime.now().month)-1
    last_month=last_month if last_month>=10 else "0"+str(last_month)

    current_year=datetime.now().year
    current_year=current_year if datetime.now().month>1 else current_year-1

    dt0="{0}-{1}-01 00:00:00".format(current_year,last_month)
    month_days=monthrange(current_year,int(last_month))[1]
    dt1="{0}-{1}-{2} 23:59:59".format(current_year,last_month,month_days)
    start_date=datetime.strptime(str(dt0),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')
    end_date=datetime.strptime(str(dt1),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%dT%H:%M:%S')

    return start_date, end_date

  def __buildBaseURL(self):
    if self.TARGET=="focuses":
      host="queimadas.dgi.inpe.br/queimadas"
      schema="https"
    else:
      host="terrabrasilis.dpi.inpe.br"
      schema="http"
    
    url="{0}://{1}/geoserver/{2}/{3}/wfs".format(schema,host,self.WORKSPACE_NAME,self.LAYER_NAME)
    return url

  def __buildQueryString(self, OUTPUTFORMAT=None):
    if self.TARGET=="focuses":
      return self.__buildFocusesQueryString(OUTPUTFORMAT)
    else:
      return self.__buildAlertsQueryString(OUTPUTFORMAT)

  def __buildAlertsQueryString(self, OUTPUTFORMAT=None):
    """
    Building the query string to call the WFS service for DETER alerts.

    The parameter: OUTPUTFORMAT, the output format for the WFS GetFeature operation described
    in the AllowedValues ​​section in the capabilities document.
    """
    # Filters example (by date interval and uf)
    CQL_FILTER="date BETWEEN '{0}' AND '{1}'".format(self.START_DATE,self.END_DATE)
    # WFS parameters
    SERVICE="WFS"
    REQUEST="GetFeature"
    VERSION="2.0.0"
    # if OUTPUTFORMAT is changed, check the output file extension within the get method in this class.
    OUTPUTFORMAT= ("SHAPE-ZIP" if not OUTPUTFORMAT else OUTPUTFORMAT)
    exceptions="text/xml"
    # define the output projection. We use the layer projection. (Geography/SIRGAS2000)
    srsName="EPSG:4674"
    # the layer definition
    TYPENAME="{0}:{1}".format(self.WORKSPACE_NAME,self.LAYER_NAME)
    
    allLocalParams=locals()
    allLocalParams.pop("self",None)
    PARAMS="&".join("{}={}".format(k,v) for k,v in allLocalParams.items())
    return PARAMS

  def __buildFocusesQueryString(self, OUTPUTFORMAT=None):
    """
    Building the query string to call the WFS service for focuses of fire.

    The parameter: OUTPUTFORMAT, the output format for the WFS GetFeature operation described
    in the AllowedValues ​​section in the capabilities document.
    """
    # WFS parameters
    SERVICE="WFS"
    REQUEST="GetFeature"
    VERSION="2.0.0"
    # if OUTPUTFORMAT is changed, check the output file extension within the get method in this class.
    OUTPUTFORMAT= ("SHAPE-ZIP" if not OUTPUTFORMAT else OUTPUTFORMAT)
    exceptions="text/xml"
    # define the output projection. We use the layer default projection. (Geography/SIRGAS2000)
    srsName="EPSG:4674"
    # the layer definition
    TYPENAME="{0}:{1}".format(self.WORKSPACE_NAME,self.LAYER_NAME)

    CQL_FILTER="data_hora_gmt between {0} AND {1}".format(self.START_DATE,self.END_DATE)
    CQL_FILTER="{0} AND satelite='AQUA_M-T' AND continente_id=8".format(CQL_FILTER)
    CQL_FILTER="{0} AND pais_complete_id=33 AND id_area_industrial=0".format(CQL_FILTER)
    CQL_FILTER="{0} AND id_tipo_area_industrial NOT IN (1,2,3,4,5)".format(CQL_FILTER)
    CQL_FILTER="{0} AND bioma='Amazônia'".format(CQL_FILTER)
    
    allLocalParams=locals()
    allLocalParams.pop("self",None)
    PARAMS="&".join("{}={}".format(k,v) for k,v in allLocalParams.items())

    return PARAMS

  def __xmlRequest(self, url):
    root=None
    if self.AUTH:
      response=requests.get(url, auth=self.AUTH)
    else:
      response=requests.get(url)
    
    if response.ok:
      xmlInMemory = io.BytesIO(response.content)
      tree = xmlTree.parse(xmlInMemory)
      root = tree.getroot()
    
    return root

  def __getServerLimit(self):
    """
    Read the data download service limit via WFS

    serverLimit: Optional parameter to inform the default limit on GeoServer
    """
    serverLimit=self.serverLimitByTarget
    url="{0}?{1}".format(self.__buildBaseURL(),"service=wfs&version=2.0.0&request=GetCapabilities")

    XML=self.__xmlRequest(url)

    if '{http://www.opengis.net/wfs/2.0}WFS_Capabilities'==XML.tag:
      for p in XML.findall(".//{http://www.opengis.net/ows/1.1}Operation/[@name='GetFeature']"):
        dv=p.find(".//{http://www.opengis.net/ows/1.1}Constraint/[@name='CountDefault']")
        serverLimit=dv.find('.//{http://www.opengis.net/ows/1.1}DefaultValue').text

    return int(serverLimit)

  def __countMaxResult(self):
    """
    Read the number of lines of results expected in the download using the defined filters.
    """
    url="{0}?{1}".format(self.__buildBaseURL(), self.__buildQueryString())
    url="{0}&{1}".format(url,"resultType=hits")
    numberMatched=0
    XML=self.__xmlRequest(url)
    if '{http://www.opengis.net/wfs/2.0}FeatureCollection'==XML.tag:
      numberMatched=XML.find('[@numberMatched]').get('numberMatched')

    return int(numberMatched)

  def __pagination(self):
    self.__configForTarget()
    # get server limit and count max number of results
    sl=self.__getServerLimit()
    rr=self.__countMaxResult()
    # store global to use on metadata
    self.numberMatched=rr
    # define the start page number
    pagNumber=1
    # define the start index of data
    startIndex=0
    # define the attribute to sort data
    sortBy=( "id_foco_bdq" if self.TARGET=="focuses" else "gid" )
    # using the server limit to each download
    count=sl
    # pagination iteraction
    while(startIndex<rr):
      paginationParams="&count={0}&sortBy={1}&startIndex={2}".format(count,sortBy,startIndex)
      self.__download(paginationParams,pagNumber)
      startIndex=startIndex+count
      pagNumber=pagNumber+1

  def __download(self, pagination="startIndex=0", pagNumber=1):
    url="{0}?{1}&{2}".format(self.__buildBaseURL(), self.__buildQueryString(), pagination)

    # the extension of output file is ".zip" because the OUTPUTFORMAT is defined as "SHAPE-ZIP"
    output_file="{0}/{1}_part{2}.zip".format(self.DATA_DIR, self.OUTPUT_FILENAME, pagNumber)
    if self.AUTH:
      response=requests.get(url, auth=self.AUTH)
    else:
      response=requests.get(url)

    if response.ok:
      with open(output_file, 'wb') as f:
        f.write(response.content)
    else:
      print("Download fail with HTTP Error: {0}".format(response.status_code))

  def __setMetadataResults(self):
    """
    Write start date, end date and number of focuses matched to use on shell script import process
    """
    output_file="{0}/acquisition_data_control".format(self.DATA_DIR)
    with open(output_file, 'w') as f:
      f.write("START_DATE=\"{0}\"\n".format(self.START_DATE))
      f.write("END_DATE=\"{0}\"\n".format(self.END_DATE))
      f.write("numberMatched={0}".format(self.numberMatched))

  def getFocuses(self):
    # download Focuses of fire
    self.TARGET="focuses"
    self.__pagination()
    # used to write some information into a file that used for import data process
    self.__setMetadataResults()

  def getAlerts(self):
    # download DETER Alerts
    self.TARGET="alerts"
    self.__pagination()
    # used to write some information into a file that used for import data process
    self.__setMetadataResults()

  def get(self):
    self.getFocuses()
    self.getAlerts()

# end of class

down=DownloadWFS()
# Call download for get all data
down.get()
