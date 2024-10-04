"""
Copyright 2024 TerraBrasilis

Usage:
  copy-data.py
"""
from osgeo import gdal
from python.psqldb import PsqlDB, QueryError
import os, sys, getopt

class ClassifyData:
  """
    Set settings at instantiation.

    This code obtains a set of focuses from the database, crosses them with the
    Deforestation RASTER data and stores the results in the database.

    Deforestation RASTER data must be prepared by an external process that involves manual steps.
  """

  def __init__(self, data_type='prodes', data_dir='./', biome='',  output_table="focos_aqua_referencia"):
    """
    Constructor with predefined settings.
    
    """
    self.DATA_TYPE=data_type
    self.DATA_DIR=data_dir
    self.BIOME=biome
    self.OUTPUT_TABLE=output_table

    self.RASTER_FILE_NAME = ""
    if self.DATA_TYPE=="prodes":
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/prodes_agregado_{self.BIOME}.tif" #prodes raster file
    else:
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/car_br_20230426.tif" #car raster file

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
      # sql to get unclassified focuses based on biome
      sql = f"SELECT uuid,latitude,longitude FROM {self.OUTPUT_TABLE} "
      sql = f"{sql} WHERE classe_{self.DATA_TYPE} = '0' AND bioma='{self.BIOME}' "
      sql = f"{sql} ORDER BY uuid asc"
      focuses = self.db.fetchData(sql)

      for focus in focuses:
        uuid = str(focus[0])
        lat = float(focus[1])
        lon = float(focus[2])
        col = int((lon - xOrigin) / pixelWidth)
        row = int((yOrigin - lat ) / pixelHeight)
        pixelvalue = data[row][col]
        query = f"UPDATE focos_aqua_referencia SET classe_{self.DATA_TYPE} = '{classes[self.DATA_TYPE][pixelvalue]}' WHERE uuid = {uuid};"

        self.db.execQuery(query=query)

      # if you have unclassified values for any focus, set the default value.
      if self.DATA_TYPE=="prodes":
        default_value=classes[self.DATA_TYPE][91]
      else:
        default_value=classes[self.DATA_TYPE][1]

      query = f"UPDATE public.focos_aqua_referencia SET classe_{self.DATA_TYPE}='{default_value}'"
      query = f"{query} WHERE classe_{self.DATA_TYPE} '0';"
      self.db.execQuery(query=query)

      self.db.commit()

    except QueryError:
      print(f"Failure on classify focuses for {self.BIOME} versus {self.DATA_TYPE}")
    finally:
      self.db.close()

# End of class

def main(argv):
    data_type = ''
    data_dir = ''
    biome = ''
    try:
      opts, args = getopt.getopt(argv,"hD:t:b:",["dir=", "type=", "biome="])
    except getopt.GetoptError:
      print("classify_data.py -t <prodes or car> -b <biome name> -D <data_dir>")
      sys.exit(2)
    for opt, arg in opts:
      if opt == '-h':
        print("classify_data.py -t <prodes or car> -b <biome name> -D <data_dir>")
        sys.exit()
      elif opt in ("-t", "--type"):
        data_type = arg
      elif opt in ("-D", "--dir"):
        data_dir = arg
      elif opt in ("-b", "--biome"):
        biome = arg

    cld=ClassifyData(data_type=data_type, data_dir=data_dir, biome=biome)
    cld.run()

if __name__ == "__main__":
  main(sys.argv[1:])