"""
Copyright 2024 TerraBrasilis

Usage:
  copy-data.py
"""

import os
from datetime import datetime, timedelta
from psqldb import PsqlDB
from config_loader import ConfigLoader


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
    # last prodes year by default
    previous_year=datetime.today().year-1
    dt0="{0}-08-01 00:00:00".format(previous_year)
    last_prodes=datetime.strptime(str(dt0),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')
    # try get from env, otherwise use default
    self.DETER_VIEW_DATE=os.getenv("DETER_VIEW_DATE", last_prodes)
    # the start date of the active fire time series used in the Fire Dashboard
    self.FIRES_START_DATE='2018-08-01'

    # Local database where data is copied to
    self.db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.db = PsqlDB(self.db_conf_file,'db.cfg','fires_dashboard')
    self.db.connect()

    # the database sources to get input data
    self.SOURCE_DBS=["deter_amazonia","deter_cerrado","deter_pantanal","raw_fires_data"]
    self.SOURCE_NAMES={
      "deter_amazonia":"Amazônia",
      "deter_cerrado":"Cerrado",
      "deter_pantanal":"Pantanal",
      "raw_fires_data":"Queimadas"
    }

  def __getLastMonthDate(self):
    """
    Get the date of the first day of the last month.
    """
    previous_month = (datetime.today().replace(day=1) - timedelta(days=1)).month
    year = datetime.today().year if datetime.today().month>1 else datetime.today().year-1
    dt = "{0}-{1}-01 00:00:00".format(year,previous_month)

    return datetime.strptime(str(dt),'%Y-%m-%d %H:%M:%S').strftime('%Y-%m-%d')

  def __loadConfigurationsFor(self, config_path, filename, section):
    """
    Load connection parameters for each database from db.cfg configuration file.
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

      # load connection parameters for each database
      self.__loadConfigurationsFor(self.db_conf_file, 'db.cfg', db)

      # make DBLink as string
      db_link = f"""hostaddr={self.params["host"]} port={self.params["port"]} dbname={self.params["dbname"]} user={self.params["user"]} password={self.params["password"]}"""
      
      # build SQL to DETER or Ative Fires data.
      if db.startswith("deter"):
        sql_view = self.__getDeterSqlView(db=db, db_link=db_link)
      elif db.startswith("raw"):
        sql_view = self.__getFiresSqlView(db=db, db_link=db_link)
      
      # add View into local database
      self.db.execQuery(sql_view)
    # to keep the Views into database
    self.db.commit()

  def __getDeterSqlView(self, db, db_link):
    """
    Make a SQLView string.

    It relies on the SQLView, called 'public.deter_fires_dashboard', existing in each origin database to normalize this access.
    """
    # make SQLView as string
    sql_view = f"CREATE OR REPLACE VIEW public.{db}_online "
    sql_view = f"{sql_view} AS "
    sql_view = f"{sql_view} SELECT  "
    sql_view = f"{sql_view}    {db}_online.class_name, "
    sql_view = f"{sql_view}    {db}_online.view_date, "
    sql_view = f"{sql_view}    st_multi({db}_online.geom)::geometry(MultiPolygon,4674) AS geom "
    sql_view = f"{sql_view}   FROM dblink('{db_link}'::text, "
    sql_view = f"{sql_view}   'SELECT class_name, view_date, geom FROM public.deter_fires_dashboard'::text) "
    sql_view = f"{sql_view}   {db}_online(class_name text, view_date date, geom geometry); "

    return sql_view


  def __getFiresSqlView(self, db, db_link):
    """
    Make a SQLView string.

    It relies on the table, called 'public.focos_aqua_referencia', existing on origin database to guarantee this access.
    """

    sql_view = f"CREATE OR REPLACE VIEW public.{db}_online "
    sql_view = f"{sql_view} AS "
    sql_view = f"{sql_view} SELECT {db}_online.fid, "
    sql_view = f"{sql_view}    {db}_online.data, "
    sql_view = f"{sql_view}    {db}_online.uuid, "
    sql_view = f"{sql_view}    {db}_online.satelite, "
    sql_view = f"{sql_view}    {db}_online.pais, "
    sql_view = f"{sql_view}    {db}_online.estado, "
    sql_view = f"{sql_view}    {db}_online.municipio, "
    sql_view = f"{sql_view}    {db}_online.bioma, "
    sql_view = f"{sql_view}    {db}_online.latitude, "
    sql_view = f"{sql_view}    {db}_online.longitude, "
    sql_view = f"{sql_view}    {db}_online.geom, "
    sql_view = f"{sql_view}    {db}_online.imported_at "
    sql_view = f"{sql_view}  FROM dblink('{db_link}'::text, "
    sql_view = f"{sql_view}   'SELECT fid, uuid, data, satelite, pais, estado, municipio, bioma, latitude, "
    sql_view = f"{sql_view}    longitude, geom, imported_at "
    sql_view = f"{sql_view}    FROM public.focos_aqua_referencia'::text) "
    sql_view = f"{sql_view}    {db}_online(fid integer, uuid character varying, data date, satelite character varying, pais character varying, "
    sql_view = f"{sql_view}    estado character varying, municipio character varying, bioma character varying, latitude double precision, "
    sql_view = f"{sql_view}    longitude double precision, geom geometry, imported_at date);"

    return sql_view
  
  def __copyData(self):
    """
    Copy DETER data and Active Fires data to local database.
    """
    for db in self.SOURCE_DBS:
      self.__copyDETERData(db) if db.startswith("deter") else self.__copyFIRESData(db)


  def __copyDETERData(self, db):
    """
    Copy DETER data by biome from source databases.
    Uses the most recent date from local database as the starting date to complete the data to date.

    If the local table is empty, uses the DETER_VIEW_DATE as start date.
    """
    select = f"""
              SELECT MAX(view_date) as start_date
              FROM public.deter
              WHERE biome='{self.SOURCE_NAMES[db]}'
            """

    res = self.db.fetchData(query=select)

    if len(res[0])>0 and res[0][0] is not None:
      start_date = res[0][0]
      op = ">"
    else:
      start_date = self.DETER_VIEW_DATE
      op = ">="

    from_where = f"""
                FROM public.{db}_online
                WHERE class_name IN ('DESMATAMENTO_VEG','DESMATAMENTO_CR','MINERACAO','supressão com vegetação','mineração','supressão com solo exposto')
                AND view_date {op} '{start_date}'::date
              """
    select = f"""
            SELECT MIN(view_date) as start_date, MAX(view_date) as end_date, COUNT(*) as num_rows
            {from_where}
          """
    res = self.db.fetchData(query=select)

    num_rows = 0
    end_date = start_date
    if len(res[0])>0 and res[0][0] is not None:
      start_date = res[0][0]
      end_date = res[0][1]
      num_rows = res[0][2]

    insert = f"""
              INSERT INTO public.deter(class_name, view_date, geom, biome)
              SELECT class_name, view_date, geom, '{self.SOURCE_NAMES[db]}'
              {from_where}
            """

    inserted_rows=self.db.execQuery(query=insert, isInsert=True)

    if inserted_rows==num_rows:
      self.__registryInControl(start_date=start_date, end_date=end_date, num_rows=num_rows, origin_data=db)
      self.db.commit()
    else:
      print(f"Failure on copy DETER data to {db}")
      print(f"The counted lines are different from the entered lines. num_rows={num_rows}, inserted_rows={inserted_rows}")
      self.db.rollback()

  def __deleteFiresLastMonthData(self):
    """
    Active fire data may have changed over the past few days, so we've excluded the last month to ensure it's up-to-date.
    """
    delete = f"""
              DELETE FROM public.focos_aqua_referencia
	            WHERE data >= '{self.__getLastMonthDate()}'::date;
            """
    self.db.execQuery(query=delete)
    self.db.commit()

  def __copyFIRESData(self, db):
    """
    Copy Active Fires data from source database.
    Uses the most recent date from local database as the starting date to complete the data to date.

    It deletes all previous month's data from the local table before proceeding with the copy.

    If the local table is empty, uses the FIRES_START_DATE as start date.
    """

    # remove the past month data because the past may be change
    self.__deleteFiresLastMonthData()

    select = f"""
              SELECT MAX(data) as start_date
              FROM public.focos_aqua_referencia
            """

    res = self.db.fetchData(query=select)

    if len(res[0])>0 and res[0][0] is not None:
      start_date = res[0][0]
      op = ">"
    else:
      start_date = self.FIRES_START_DATE
      op = ">="

    from_where = f"""
                  FROM public.{db}_online
                  WHERE data {op} '{start_date}'::date
                """
    select = f"""
              SELECT MIN(data) as start_date, MAX(data) as end_date, COUNT(*) as num_rows
              {from_where}
            """
    res = self.db.fetchData(query=select)

    num_rows = 0
    end_date = start_date
    if len(res[0])>0 and res[0][0] is not None:
      start_date = res[0][0]
      end_date = res[0][1]
      num_rows = res[0][2]

    insert = f"""
              INSERT INTO public.focos_aqua_referencia(uuid, data, satelite, pais, estado, municipio, bioma, latitude, longitude, geom)
              SELECT uuid, data, satelite, pais, estado, municipio, bioma, latitude, longitude, geom
              {from_where}
            """

    inserted_rows=self.db.execQuery(query=insert, isInsert=True)

    if inserted_rows==num_rows:
      self.__registryInControl(start_date=start_date, end_date=end_date, num_rows=num_rows, origin_data=db)
      self.db.commit()
    else:
      print(f"Failure on copy Active Fires data to {db}")
      print(f"The counted lines are different from the entered lines. num_rows={num_rows}, inserted_rows={inserted_rows}")
      self.db.rollback()

  def __registryInControl(self, start_date, end_date, num_rows, origin_data):
    """
    Logs the copy operation.
    """
    sql = f"""INSERT INTO public.acquisition_data_control(
          start_date, end_date, num_rows, origin_data)
          VALUES ('{start_date}', '{end_date}', {num_rows}, '{origin_data}');
          """
    self.db.execQuery(sql)

  def __clearOldDETERData(self):
    """
    Delete old data in the local DETER table using DETER_VIEW_DATE.
    If there is data before the DETER_VIEW_DATE date, it will be deleted.
    """

    sql = f"DELETE FROM public.deter WHERE view_date < '{self.DETER_VIEW_DATE}';"
    
    self.db.execQuery(sql)
  
  def __dropSQLViews(self):
    """
    Remove the SQL Views from local database.
    """
    for db in self.SOURCE_DBS:

      sql = f"DROP VIEW public.{db}_online;"
      
      # Drop View from local database
      self.db.execQuery(sql)
    self.db.commit()
  

  def run(self):
    try:
      # Clear the local DETER table if DETER_VIEW_DATE changes to a more recent date.
      self.__clearOldDETERData()
      self.__createSqlViews()
      self.__copyData()
      self.__dropSQLViews()
    except Exception as error:
      print("There was an error when trying to copy data.")
      print(error)
      self.db.rollback()

# end of class

# Call for get all data
cpd=CopyData()
cpd.run()