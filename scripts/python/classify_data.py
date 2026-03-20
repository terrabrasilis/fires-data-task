"""
Copyright 2024 TerraBrasilis

Usage:
  classify_data.py
"""
from osgeo import gdal
from psqldb import PsqlDB, QueryError, ConnectionError
from alive_progress import alive_bar
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

    Use the following environment variables to change the default values.

      - DATA_TYPE, To define which data will be processed. There are two option: prodes (default) or car.
      - DATA_DIR, To set the location where the input files are. Default is the relative data directory where this script is '../../data', usually used for debugging.
      - BLOCK_SIZE, To change the block size, it is used to read the raster file by blocks. The default is 100 lines.
      - OUTPUT_TABLE, To define the name of the output table where the focuses are read and the classification results are written. Default is public.focos_aqua_referencia.
    """
    self.DATA_TYPE = os.getenv("DATA_TYPE", "prodes")
    self.DATA_DIR = os.getenv("DATA_DIR", os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data')
    self.BLOCK_SIZE = int(os.getenv("BLOCK_SIZE", 100))
    self.OUTPUT_TABLE = os.getenv("OUTPUT_TABLE", "public.focos_aqua_referencia")

    self.CLASSES = {
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

    self.RASTER_FILE_NAME = ""
    if self.DATA_TYPE=="prodes":
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/fires_dashboard_prodes.tif" # supression (prodes+deter) raster file
    else:
      self.RASTER_FILE_NAME = f"{self.DATA_DIR}/car_br_20230426.tif" # car raster file

    if not os.path.isfile(self.RASTER_FILE_NAME):
      raise Exception(f"File not found: {self.RASTER_FILE_NAME}")

    db_conf_file = os.path.realpath(os.path.dirname(__file__) + '/../../') + '/data/config/'
    self.db = PsqlDB(db_conf_file,'db.cfg','fires_dashboard')

  def run(self):

    try:
      self.db.connect()

      # load geotiff metadata
      dataset = gdal.Open(self.RASTER_FILE_NAME)
      band = dataset.GetRasterBand(1)

      transform = dataset.GetGeoTransform()

      # define the block size
      x_block_size = dataset.RasterXSize
      y_block_size = 100 # force block to this amount of lines

      self.__classify_by_blocks(x_block_size=x_block_size, y_block_size=y_block_size, transform=transform, band=band, db=self.db)
      self.__set_to_default_classname()
      self.db.commit()
    
    except QueryError as qe:
      self.db.rollback()
      print(f"Failure on classify focuses versus {self.DATA_TYPE}")
      print(f"QueryError: {qe}")
    except ConnectionError as ce:
      print(f"Failure on connect to database.")
      print(f"ConnectionError: {ce}")
    except Exception as ex:
      print(f"Failure on read raster file. Error: {ex}")
    finally:
      self.db.close()

  def __classify_by_blocks(self, x_block_size, y_block_size, transform, band, db: PsqlDB):
    """
    Read the raster as array for the chosen block size, gets the focuses that are inside the current block,
    gets the pixel value for each focus and update in database focuses table.
    """

    # read metadata of input raster file
    xOrigin = transform[0]
    yOrigin = transform[3]
    pixelWidth = transform[1]
    pixelHeight = -transform[5]

    # read total raster XY size.
    xsize = band.XSize
    ysize = band.YSize

    blocks = int(ysize/y_block_size) # total blocks to print percentage of process
    with alive_bar(blocks, title=f"Classifying focuses versus {self.DATA_TYPE}") as bar:
      for y in range(0, ysize, y_block_size):
        
        if y + y_block_size < ysize:
          rows = y_block_size
        else:
          rows = ysize - y
          
        query = ""
        for x in range(0, xsize, x_block_size):
          if x + x_block_size < xsize:
            cols = x_block_size
          else:
            cols = xsize - x

          try:
            # read one block to memory
            data = band.ReadAsArray(x, y, cols, rows)

            xMin_lon = x * pixelWidth + xOrigin
            xMax_lon = cols * pixelWidth + xOrigin
            yMax_lat = yOrigin - y * pixelHeight
            yMin_lat = yOrigin - ((y+rows) * pixelHeight)

            focuses = self.__get_focuses_by_block(db=db, xmax=xMax_lon, xmin=xMin_lon, ymax=yMax_lat, ymin=yMin_lat)
        
            for focus in focuses:
              uuid = str(focus[0])
              lat = float(focus[1])
              lon = float(focus[2])
              col = int((lon - xOrigin) / pixelWidth)
              row = int((yMax_lat - lat) / pixelHeight)
              class_name = self.CLASSES[self.DATA_TYPE][data[row][col]] if data[row][col]>0 else self.__get_default_classname()

              query = f"{query} UPDATE {self.OUTPUT_TABLE} SET classe_{self.DATA_TYPE} = '{class_name}',"
              query = f"{query} updated_at=(now())::date WHERE uuid = '{uuid}';"

          except Exception as ex:
            print(f"Error: {ex}")
          
          # send the update of the current block's focuses to the database
          if not "".__eq__(query):
            db.execQuery(query=query)

          del data
          bar()
          blocks -= 1

  def __get_focuses_by_block(self, db: PsqlDB, xmin, ymax, xmax, ymin):
    """
    Gets the unclassified focuses using a bounding box for one raster block.
    """
    # sql to get unclassified focuses
    sql = f"SELECT uuid,latitude,longitude FROM {self.OUTPUT_TABLE} "
    sql = f"{sql} WHERE classe_{self.DATA_TYPE} = '0' AND latitude >= {ymin} AND latitude <= {ymax} "
    sql = f"{sql} AND longitude >= {xmin} AND longitude <= {xmax} AND bioma IS NOT NULL;"

    focuses = db.fetchData(sql)
    return focuses

  def __get_default_classname(self):
    if self.DATA_TYPE=="prodes":
      default_value=self.CLASSES[self.DATA_TYPE][91]
    else:
      default_value=self.CLASSES[self.DATA_TYPE][1]
    
    return default_value

  def __set_to_default_classname(self):
    """
    If you have unclassified values for any focus, set the default value.
    """
    query = f"UPDATE {self.OUTPUT_TABLE} SET classe_{self.DATA_TYPE}='{self.__get_default_classname()}'"
    query = f"{query} WHERE classe_{self.DATA_TYPE} = '0';"
    self.db.execQuery(query=query)

# End of class

# start classify process
cld=ClassifyData()
cld.run()
