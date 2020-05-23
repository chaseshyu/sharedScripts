#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#  photo2kml.py
#  convert photo's metadata to kml for mapping.
#
#  Created by Chase J. Shyu on May 23rd, 2020.
# Environment dependency:
#   python-pykml, PIL, 
import sys, time, glob, math
from pykml.factory import KML_ElementMaker as KML
from lxml import etree
from PIL import Image

trip_name = "Good Trip 2020"

tag_dict = {'GPSInfo': 34853,
            'DateTime':306,
            'Model':272}

def exiftool(files,tag_ind):

  metadata = []
  inc = False
  for imagename in files:
    # read the image data using PIL
    try:
      image = Image.open(imagename)
    except IOError:
      continue
    # extract EXIF data
    exifdata = image.getexif()
    try:
      m = [exifdata[t] for t in tag_ind]
      coord = m[0]
      lat = coord[2][0][0] + coord[2][1][0]/coord[2][1][1]/60. + coord[2][2][0]/coord[2][2][1]/3600.
      lon = coord[4][0][0] + coord[4][1][0]/coord[4][1][1]/60. + coord[4][2][0]/coord[4][2][1]/3600.
      preci = coord[2][1][1]*60.
      if preci < coord[2][2][1]*3600.:
        preci = coord[2][2][1]*3600.
      preci = int(math.log10(preci))
      if coord[1] == 'S':
        lat = -lat
      if coord[3] == 'W':
        lon = -lon
      coord_text = '%s, %s' % (round(lon, preci),round(lat, preci))
    except KeyError:
      print('Warning: No GPSInfo metadata: %s Skipped.' % imagename)
      continue
    try:
      datetime = m[1]
    except KeyError:
      print('Warning: No DateTime metadata: %s Replace by 1900:01:01 00:00:01.' % imagename)
      datetime = '1900:01:01 00:00:01'
    try:
      model = m[2]
    except KeyError:
      print('Warning: No Model metadata: %s Replaced by N/A.' + imagename)
      model = 'N/A'      
    metadata.append([imagename, coord_text, datetime, model])
    inc = True
  return metadata, inc

def photo2kml(files,tags):
  tag_inds = [tag_dict[t] for t in tags]
  metadata, inc = exiftool(files,tag_inds)
  if not inc:
    sys.exit('Error: File not found.')

  time_list = [time.strptime(m[2], "%Y:%m:%d %H:%M:%S") for m in metadata]
  sort_index = sorted(range(len(time_list)), key=lambda k: time_list[k])

  kml = KML.Folder(KML.name(trip_name))
  for i in sort_index:
    meta = metadata[i]
    meta[0] = meta[0][2:]
    kml.append(
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

  return kml

def main():
  path = '.'
  if len(sys.argv) > 1:
    path = sys.argv[1]

  files = glob.glob(path + '/*')
  tags = ['GPSInfo','DateTime','Model']

  kml_folder = photo2kml(files,tags)

  with open(trip_name+'.kml','w') as f:
    #print(etree.tostring(fld, pretty_print=True).decode('UTF-8'))
    f.write(etree.tostring(kml_folder, pretty_print=True).decode('UTF-8'))
  print('photo2kml convertion finished.\n')

if __name__ == '__main__':
  main()

