#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#  photo2kml.py
#  convert photo's metadata to kml for mapping.
#
#  Created by Chase J. Shyu on May 23rd, 2020.
# Environment dependency:
#   python-pykml, PIL

import sys, time, glob, math
from pykml.factory import KML_ElementMaker as KML
from lxml import etree
from PIL import Image

trip_name = "Good Trip 2020"
# choose icon url from http://kml4earth.appspot.com/icons.html
icon_url = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png'

# choose tags
meta_tags = ['GPSInfo','DateTime','Model']

# Standard Exif Tags from https://www.exiv2.org/tags.html
tag_dict = {'GPSInfo': 34853,
            'DateTime':306,
            'Model':272}

def exiftool(files,tag_inds):

  metadata = []
  inc = False
  for imagename in files:
    try:
      image = Image.open(imagename)
    except IOError:
      continue

    exifdata = image.getexif()
    try:
      coord = exifdata[tag_inds[0]]
      lat = coord[2][0][0]/coord[2][0][1] 
      lat += coord[2][1][0]/coord[2][1][1]/60. 
      lat += coord[2][2][0]/coord[2][2][1]/3600.
      lon = coord[4][0][0]/coord[4][0][1]
      lon += coord[4][1][0]/coord[4][1][1]/60. 
      lon += coord[4][2][0]/coord[4][2][1]/3600.

      if lat > 90. or lon > 180.:
        print('Error: GPSInfo metadate out of range: %s' % imagename)

      preci = coord[2][1][1]*60.
      if preci < coord[2][2][1]*3600.:
        preci = coord[2][2][1]*3600.
      preci = int(math.log10(preci))
      if coord[1] == 'S':
        lat = -lat
      if coord[3] == 'W':
        lon = -lon

    except KeyError:
      print('Warning: No GPSInfo metadata: %s Skipped.' % imagename)
      continue

    try:
      datetime = exifdata[tag_inds[1]]
    except KeyError:
      print('Warning: No DateTime metadata: %s Replace by 1900:01:01 00:00:01.' % imagename)
      datetime = '1900:01:01 00:00:01'

    try:
      model = exifdata[tag_inds[2]]
    except KeyError:
      print('Warning: No Model metadata: %s Replaced by N/A.' + imagename)
      model = 'N/A'

    metadata.append([imagename, round(lon, preci), round(lat, preci), datetime, model])
    inc = True
  return metadata, inc

def photo2kml(files,tags):
  tag_inds = [tag_dict[t] for t in tags]
  metadata, inc = exiftool(files,tag_inds)
  if not inc:
    sys.exit('Error: File not found.')

  time_list = [time.strptime(m[3], "%Y:%m:%d %H:%M:%S") for m in metadata]
  sort_index = sorted(range(len(time_list)), key=lambda k: time_list[k])

  kml_doc = KML.kml(
      KML.Document(
          KML.name(trip_name),
          KML.Style(
              KML.IconStyle(
                  KML.scale(1.),
                  KML.Icon(
                      KML.href(icon_url)
                  ),
              ),
              id='icon_style',
          )
      )
  )

  for i in sort_index:
    meta = metadata[i]
    meta[0] = meta[0].replace('./','')
    coord_text = '%f, %s' % (meta[1],meta[2])

    kml_doc.Document.append(
      KML.Placemark(
        KML.name(meta[3]),
        KML.styleUrl('#{0}'.format('icon_style')),
        KML.description('Photo location'),
        KML.Point(KML.coordinates(coord_text)),
        KML.ExtendedData(
          KML.Data(KML.value(trip_name),name='Trip'),
          KML.Data(KML.value(meta[3]),name='Time'),
          KML.Data(KML.value(meta[4]),name='Model'),
          KML.Data(KML.value(meta[0]),name='Name'),
        )
      )
    )
  return kml_doc, len(sort_index)

def main():
  path = './'
  if len(sys.argv) > 1:
    path = sys.argv[1] + '/'

  files = glob.glob(path + '*')

  kml_doc, inc = photo2kml(files,meta_tags)

  with open(trip_name+'.kml','w') as f:
    #print(etree.tostring(kml_doc, pretty_print=True).decode('UTF-8'))
    f.write(etree.tostring(kml_doc, pretty_print=True).decode('UTF-8'))

  print('photo2kml convertion finished: %d position(s).\n' % inc)

if __name__ == '__main__':
  main()

