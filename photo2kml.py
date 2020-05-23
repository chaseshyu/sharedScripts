#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#  photo2kml.py
#  convert photo's metadata to kml for mapping.
#
#  Created by Chase J. Shyu on May 23rd, 2020.
# Environment dependency:
#   python-pykml
import sys, time, glob
from pykml.factory import KML_ElementMaker as KML
from lxml import etree
from PIL import Image

trip_name = "Good Trip 2020"

tag_ind = {'GPSInfo': 34853,
            'DateTime':306,
            'Model':272}

def exiftool(files,tags):

  metadata = []
  inc = False
  for imagename in files:
    # read the image data using PIL
    try:
      image = Image.open(imagename)
    except IOError:
      continue
    inc = True
    # extract EXIF data
    exifdata = image.getexif()
    m = [exifdata[tag_ind[t]] for t in tags]
    coord = m[0]
    lat = coord[2][0][0] + coord[2][1][0]/60. + coord[2][2][0]/360000.
    lon = coord[4][0][0] + coord[4][1][0]/60. + coord[4][2][0]/360000.
    if coord[1] == 'S':
      lat = -lat
    if coord[3] == 'W':
      lon = -lon
    coord_text = '%.7f, %.7f' % (lon,lat)
    metadata.append([imagename,coord_text,m[1],m[2]])

  return metadata, inc

def main(path='./'):

  files = glob.glob(path + '/*')
  tags = ['GPSInfo','DateTime','Model']
  metadata, inc = exiftool(files,tags)
  if not inc:
    sys.exit('Error: File not found.')

  time_list = [time.strptime(m[2], "%Y:%m:%d %H:%M:%S") for m in metadata]
  sort_index = sorted(range(len(time_list)), key=lambda k: time_list[k])

  fld = KML.Folder(KML.name(trip_name))
  for i in sort_index:
    meta = metadata[i]
    meta[0] = meta[0][2:]
    fld.append(
      KML.Placemark(
        KML.name(meta[2]),
        KML.description('Photo location'),
        KML.Point(KML.coordinates(meta[1])),
        KML.ExtendedData(
          KML.Data(KML.value(trip_name),name='Trip'),
          KML.Data(KML.value(meta[2]),name='Time'),
          KML.Data(KML.value(meta[3]),name='Model'),
          KML.Data(KML.value(meta[0]),name='Name')
        ) 
      )
    )

  with open(trip_name+'.kml','w') as f:
    #print(etree.tostring(fld, pretty_print=True).decode('UTF-8'))
    f.write(etree.tostring(fld, pretty_print=True).decode('UTF-8'))
  print('photo2kml convertion finished.\n')

if __name__ == '__main__':
  path = './'
  if len(sys.argv) > 1:
    path = sys.argv[1]
  main(path)

