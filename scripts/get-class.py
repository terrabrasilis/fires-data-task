"""
Created on Thu Sep 24 11:20:25 2020

@author: Luis Maurano
"""

from osgeo import gdal
import psycopg2
import sys, getopt

def main(argv):
  host = ''
  port = ''
  database = ''
  user = ''
  password = ''
  typedata = ''
  data_dir = ''
  try:
    opts, args = getopt.getopt(argv,"hD:H:P:d:u:p:t:",["dir=", "host=","port=","dbname=","user=","pass=", "type="])
  except getopt.GetoptError:
    print("get_class.py -H <hostname or ip> -P <port number> -d <database name> -u <user> -p <password> -t <prodes or car>")
    sys.exit(2)
  for opt, arg in opts:
    if opt == '-h':
      print("get_class.py -H <hostname or ip> -P <port number> -d <database name> -u <user> -p <password> -t <prodes or car>")
      sys.exit()
    elif opt in ("-H", "--host"):
      host = arg
    elif opt in ("-P", "--port"):
      port = arg
    elif opt in ("-d", "--dbname"):
      database = arg
    elif opt in ("-u", "--user"):
      user = arg
    elif opt in ("-p", "--pass"):
      password = arg
    elif opt in ("-t", "--type"):
      typedata = arg
    elif opt in ("-D", "--dir"):
      data_dir = arg

  #print(data_dir+" "+host+" "+port+" "+database+" "+user+" "+password+" "+typedata)
  run(host, port, database, user, password, typedata, data_dir)

def run(host='localhost', port='5432', database='dbname', user='postgres', password='postgres', typedata='prodes', data_dir='./'):
  con = psycopg2.connect("host="+host+" dbname="+database+" user="+user+" password="+password+" port="+port)

  classes_prodes = {
    0: "Outros",
    1: "Floresta",
    10: "Desmatamento Consolidado",
    15: "Desmatamento Recente"
  }
  classes_car = {
    0: "Sem CAR",
    5: "Minifundio",
    10: "Grande",
    15: "Media",
    20: "Pequena"
  }

  # tiff 
  driver = gdal.GetDriverByName('GTiff')
  filename = ""
  if typedata=="prodes":
    filename = "{0}/prodes_agregado.tif".format(data_dir) #prodes raster file
  else:
    filename = "{0}/car_categories_amz_cerrado.tif".format(data_dir) #car raster file
  
  dataset = gdal.Open(filename)
  band = dataset.GetRasterBand(1)

  cols = dataset.RasterXSize
  rows = dataset.RasterYSize

  transform = dataset.GetGeoTransform()

  xOrigin = transform[0]
  yOrigin = transform[3]
  pixelWidth = transform[1]
  pixelHeight = -transform[5]

  data = band.ReadAsArray(0, 0, cols, rows)

  #sql para pegar focos 
  sql = "SELECT id,latitude,longitude FROM focos_aqua_referencia "
  sql = "{0} WHERE longitude >= -73.9783164486977967 AND longitude <= -41.5219096 ".format(sql)
  sql = "{0} AND latitude >= -24.6847207 and latitude <= 5.2714909087058901 ".format(sql)
  sql = "{0} AND (classe_car IS NULL OR classe_prodes IS NULL) ".format(sql)
  sql = "{0} ORDER BY id asc".format(sql)
  cur = con.cursor()
  cur.execute(sql)
  campos = cur.fetchall()

  for campo in campos:
    id = str(campo[0])
    lat = float(campo[1])
    lon = float(campo[2])
    col = int((lon - xOrigin) / pixelWidth)
    row = int((yOrigin - lat ) / pixelHeight)
    pixelvalue = data[row][col]
    query = ''
    pixelclasse=''
      # trocar classe_prodes por classes_car
    if typedata=="prodes":
      pixelclasse = classes_prodes[pixelvalue]
      query = "UPDATE focos_aqua_referencia SET classe_prodes = '" + pixelclasse + "' WHERE id = " + id + ";"
    else:
      pixelclasse = classes_car[pixelvalue]
      query = "UPDATE focos_aqua_referencia SET classe_car = '" + pixelclasse + "' WHERE id = " + id + ";"

    cur.execute(query)
    print (query,id,lat,lon,pixelvalue,pixelclasse)
      
  con.commit()

  # Finally, if you have NULL values for any focus, set the default value.
  if typedata=="prodes":
    query = "UPDATE public.focos_aqua_referencia SET classe_prodes='Outros' WHERE classe_prodes IS NULL;"
  else:
    query = "UPDATE public.focos_aqua_referencia SET classe_car='Sem CAR' WHERE classe_car IS NULL;"

  cur.execute(query)
  con.commit()

  cur.close()
  con.close()

if __name__ == "__main__":
  main(sys.argv[1:])