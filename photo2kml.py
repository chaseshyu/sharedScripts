#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#  photo2kml.py
#  convert photo's metadata to kml for mapping.
#
#  Environment dependency: python-pykml, python-pillow
#
#  Created by Chase J. Shyu on May 23rd, 2020.
#  GitHub: https://github.com/chaseshyu/sharedScripts
import sys, time, glob, math, lxml
from pykml.factory import KML_ElementMaker as KML
from PIL import Image

trip_name = "Good Trip 2020"
# choose icon url from http://kml4earth.appspot.com/icons.html
icon_url = 'http://maps.google.com/mapfiles/kml/shapes/placemark_circle_highlight.png'

# choose tags
meta_tags = ['GPSInfo','DateTime','Model']

# Standard Exif Tags from https://www.exiv2.org/tags.html
tag_dict = {'GPSInfo': 34853, 'DateTime':306, 'Model':272}

def exiftool(files,tag_inds):
  metadata = []
  inc = False
  for imagename in files:
    try:
      image = Image.open(imagename)
    except IOError:
      continue

    inc = True
    exifdata = image.getexif()
    try:
      coord = exifdata[tag_inds[0]]
      preci = int(math.log10(max(coord[2][1][1]*60.,coord[2][2][1]*3600.)))
      lat = round(sum([l[0]/(l[1]*60.**i) for i,l in enumerate(coord[2])]),preci)
      lon = round(sum([l[0]/(l[1]*60.**i) for i,l in enumerate(coord[4])]),preci)
    except KeyError:
      print('Warning: %s no GPSInfo. Skipped.' % imagename)
      continue

    if lat > 90. or lon > 180.:
      sys.exit('Error: %s GPSInfo out of range. lon: %f lat: %f' % (imagename,lon,lat))

    if coord[1] == 'S': lat = -lat
    if coord[3] == 'W': lon = -lon

    try:
      datetime = exifdata[tag_inds[1]]
    except KeyError:
      print('Warning: %s no DateTime. Replace by 1900:01:01 00:00:01.' % imagename)
      datetime = '1900:01:01 00:00:01'

    try:
      model = exifdata[tag_inds[2]]
    except KeyError:
      print('Warning: %s no Model. Replaced by N/A.' % imagename)
      model = 'N/A'

    metadata.append([imagename, lon, lat, datetime, model])
  return metadata, inc

def photo2kml(files,tags):
  tag_inds = [tag_dict[t] for t in tags]
  metadata, inc = exiftool(files,tag_inds)
  if not inc:
    sys.exit('Error: File not found.')
  elif not len(metadata):
    sys.exit('Error: GPSInfo not found in file.')

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
    f.write(lxml.etree.tostring(kml_doc, pretty_print=True).decode('UTF-8'))

  print('photo2kml convertion finished: %d position(s).\n' % inc)

if __name__ == '__main__':
  main()

