"""
Copyright 2024 TerraBrasilis

Usage:
  copy-data.py
"""

import os
from datetime import datetime
from python.psqldb import PsqlDB
from python.config_loader import ConfigLoader


class CopyData:
  """
    Set settings at instantiation.

    This code creates SQLViews in the dashboard database, pointing to source databases
    such as DETER and Fire Raw Data, uses these SQLViews to load data into local tables,
    and removes the SQLViews at the end.
  """

  def __init__(self):
    """
    Constructor with predefined settings.
    
    """
    # the fisrt day of current month
    self.CURRENT_MONTH=(datetime.today().replace(day=1))
    # last prodes year by default
    previous_year=datetime.today().year-1
    dt0="{0}-08-01 00:00:00".format(previous_year)
    last_prodes=datetime.strptime(str(dt0),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    # try get from env, otherwise use default
    self.DETER_VIEW_DATE=os.getenv("DETER_VIEW_DATE", last_prodes)

    # Main database where data is copied to
    self.db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.db = PsqlDB(self.db_conf_file,'db.cfg','fires_dashboard')
    self.db.connect()

    # the database sources to get input data
    self.SOURCE_DBS=["deter_amazonia","deter_cerrado","deter_pantanal","raw_fires_data"]

  def __loadConfigurationsFor(self, config_path, filename, section):
    """
    
    """
    try:
        conf = ConfigLoader(config_path, filename, section)
        self.params = conf.get()
    except Exception as configError:
        raise configError

  def __createSqlViews(self):
    """
    Create ane SQLView to each source database that used to copy data from DETERs and raw fires database.

    Its depends of the 'public.deter_fires_dashboard' SQLView exists on each target database to normalize this access.
    """
    for db in self.SOURCE_DBS:
      self.__loadConfigurationsFor(self.db_conf_file, 'db.cfg', db)
      # make DBLink as string
      db_link = f"'hostaddr={self.params["host"]} port={self.params["port"]} dbname={self.params["dbname"]} user={self.params["user"]} password={self.params["password"]}"
      if db.startswith("deter"):
        sql_view = self.__getDeterSqlView(db=db, db_link=db_link)
      elif db.startswith("raw"):
        sql_view = self.__getFiresSqlView(db=db, db_link=db_link)
      # add View into main database
      self.db.execQuery(sql_view)

  def __getDeterSqlView(self, db, db_link):
    """
    Make a SQLView string.

    Its depends of the 'public.deter_fires_dashboard' SQLView exists on each target database to normalize this access.
    """
    # make SQLView as string
    sql_view = f"CREATE OR REPLACE VIEW public.{db}_online "
    sql_view = f" AS "
    sql_view = f" SELECT  "
    sql_view = f"    {db}_online.class_name, "
    sql_view = f"    {db}_online.view_date, "
    sql_view = f"    {db}_online.geom "
    sql_view = f"   FROM dblink('{db_link}'::text, "
    sql_view = f"   'SELECT class_name, view_date, geom FROM public.deter_fires_dashboard'::text) "
    sql_view = f"   {db}_online(class_name text, view_date date, geom geometry); "

    return sql_view


  def __getFiresSqlView(self, db, db_link):
    """
    Make a SQLView string.
    """

    sql_view = f"CREATE OR REPLACE VIEW public.{db}_online "
    sql_view = f" AS "
    sql_view = f" SELECT {db}_online.fid, "
    sql_view = f"    {db}_online.data, "
    sql_view = f"    {db}_online.uuid, "
    sql_view = f"    {db}_online.satelite, "
    sql_view = f"    {db}_online.pais, "
    sql_view = f"    {db}_online.estado, "
    sql_view = f"    {db}_online.municipio, "
    sql_view = f"    {db}_online.bioma, "
    sql_view = f"    {db}_online.latitude, "
    sql_view = f"    {db}_online.longitude, "
    sql_view = f"    {db}_online.geom, "
    sql_view = f"    {db}_online.imported_at "
    sql_view = f"  FROM dblink('{db_link}'::text, "
    sql_view = f"   'SELECT fid, uuid, data, satelite, pais, estado, municipio, bioma, latitude, "
    sql_view = f"    longitude, geom, imported_at "
    sql_view = f"    FROM public.focos_aqua_referencia'::text) "
    sql_view = f"    {db}_online(fid integer, uuid character varying, data date, satelite character varying, pais character varying, "
    sql_view = f"    estado character varying, municipio character varying, bioma character varying, latitude double precision, "
    sql_view = f"    longitude double precision, geom geometry, imported_at date);"

    return sql_view

  def __copyDETERData(self):
    """
    
    """
    # self.__registryInControl()
    pass


  def __registryInControl(self):
    """
    
    """
    pass

  def __copyFIRESData(self):
    """
    
    """
    pass

  def __dropSQLViews(self):
    """
    
    """
    pass
  

  def run(self):
    try:
      self.__createSqlViews()
      self.__copyDETERData()
      self.__copyFIRESData()
      self.__dropSQLViews()
    except Exception as error:
      print("There was an error when trying to copy data.")
      print(error)

# end of class

# Call for get all data
cpd=CopyData()
cpd.run()