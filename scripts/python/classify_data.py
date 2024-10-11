"""
Copyright 2024 TerraBrasilis

Usage:
  classify_data.py
"""
from osgeo import gdal
from psqldb import PsqlDB, QueryError
import os

class ClassifyData:
  """
    Set settings at instantiation.

    This code obtains a set of focuses from the database, crosses them with the
    Deforestation RASTER data and stores the results in the database.

    Deforestation RASTER data must be prepared by an external process that involves manual steps.
  """

  def __init__(self):
    """
    Constructor with predefined settings.
    
    """
    self.DATA_TYPE=os.getenv("DATA_TYPE", "prodes")
    self.DATA_DIR=os.getenv("DATA_DIR", "./")
    self.BIOME=os.getenv("BIOME", None)
    self.OUTPUT_TABLE=os.getenv("OUTPUT_TABLE", "focos_aqua_referencia")

    self.RASTER_FILE_NAME = ""
    if self.DATA_TYPE=="prodes":
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/prodes_agregado.tif" #prodes raster file
    else:
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/car_br_20230426.tif" #car raster file

    if not os.path.isfile(self.RASTER_FILE_NAME):
      raise Exception(f"File not found: {self.RASTER_FILE_NAME}")

    db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.db = PsqlDB(db_conf_file,'db.cfg','fires_dashboard')
    self.db.connect()

  def run(self):

    classes = {
      'prodes': {
        10: "Desmatamento Consolidado",
        11: "Desmatamento Consolidado",
        15: "Desmatamento Recente",
        16: "Desmatamento Recente",
        91: "Outros", 
        100: "Vegetacao Nativa",
        101: "Vegetacao Nativa"
      },
      'car': {
        1: "Sem car",
        10: "Pequena",
        11: "Pequena",
        15: "Media",
        16: "Media",
        20: "Grande",
        21: "Grande"
      }
    }

    # load tiff
    gdal.GetDriverByName('GTiff')
    dataset = gdal.Open(self.RASTER_FILE_NAME)
    band = dataset.GetRasterBand(1)

    cols = dataset.RasterXSize
    rows = dataset.RasterYSize

    transform = dataset.GetGeoTransform()

    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]

    data = band.ReadAsArray(0, 0, cols, rows)

    try:
      filter_by_biome="" if self.BIOME is None else f" AND bioma='{self.BIOME}'"

      # sql to get unclassified focuses based on biome
      sql = f"SELECT uuid,latitude,longitude FROM {self.OUTPUT_TABLE} "
      sql = f"{sql} WHERE classe_{self.DATA_TYPE} = '0'{filter_by_biome};"
      focuses = self.db.fetchData(sql)

      for focus in focuses:
        uuid = str(focus[0])
        lat = float(focus[1])
        lon = float(focus[2])
        col = int((lon - xOrigin) / pixelWidth)
        row = int((yOrigin - lat ) / pixelHeight)
        pixelvalue = data[row][col]
        query = f"UPDATE focos_aqua_referencia SET classe_{self.DATA_TYPE} = '{classes[self.DATA_TYPE][pixelvalue]}' WHERE uuid = '{uuid}';"

        self.db.execQuery(query=query)

      # if you have unclassified values for any focus, set the default value.
      if self.DATA_TYPE=="prodes":
        default_value=classes[self.DATA_TYPE][91]
      else:
        default_value=classes[self.DATA_TYPE][1]

      query = f"UPDATE public.focos_aqua_referencia SET classe_{self.DATA_TYPE}='{default_value}'"
      query = f"{query} WHERE classe_{self.DATA_TYPE} = '0';"
      self.db.execQuery(query=query)

      self.db.commit()

    except QueryError:
      self.db.rollback()
      print(f"Failure on classify focuses versus {self.DATA_TYPE}")
    finally:
      self.db.close()

# End of class

# start classify process
cld=ClassifyData()
cld.run()
