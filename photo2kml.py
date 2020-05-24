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
from PIL import Image
from pykml.factory import KML_ElementMaker as KML

# name of kml file and layer
trip_name = "Good Trip 2020"

# choose icon url from http://kml4earth.appspot.com/icons.html
icon_url = 'http://maps.google.com/mapfiles/kml/paddle/wht-blank.png'

# x, y fraction for icon alignment
icon_align = [0.5, 0.0]

# ARGB [transparency, blue, green, red]
icon_color = [200,211,100,148] # only valid in Google Earth

# choose tags
meta_tags = ['GPSInfo','DateTime','Model']

# Standard Exif Tags from https://www.exiv2.org/tags.html
tag_dict = {'GPSInfo': 34853, 'DateTime':306, 'Model':272}

# for convertion of coordinate
orient = {'N':1.,'E':1.,'S':-1.,'W':-1.}

# decimal - hex convertion
color_argb = "".join('%0*x'%(2,c) for c in icon_color)

def exiftool(files,tag_inds):
  inc = False
  metadata = []
  for imagename in files:
    try:
      image = Image.open(imagename)
    except IOError:
      continue

    inc = True
    exifdata = image.getexif()
    try:
      coord = exifdata[tag_inds[0]]
      lat = sum([l[0]/(l[1]*60.**i) for i,l in enumerate(coord[2])])
      lon = sum([l[0]/(l[1]*60.**i) for i,l in enumerate(coord[4])])
    except KeyError:
      print('Warning: %s no GPSInfo and skipped.' % imagename)
      continue

    if lat > 90. or lon > 180.:
      sys.exit('Error: %s GPSInfo out of range. lon: %f lat: %f' % (imagename,lon,lat))

    preci = int(math.log10(max(coord[2][1][1]*60.,coord[2][2][1]*3600.)))
    lat = round(lat*orient[coord[1]],preci)
    lon = round(lon*orient[coord[3]],preci)

    try:
      datetime = exifdata[tag_inds[1]]
    except KeyError:
      print('Warning: %s no DateTime and replace by "1900:01:01 00:00:01".' % imagename)
      datetime = '1900:01:01 00:00:01'

    try:
      model = exifdata[tag_inds[2]]
    except KeyError:
      print('Warning: %s no Model and replaced by "N/A".' % imagename)
      model = 'N/A'

    metadata.append([imagename, lon, lat, datetime, model])
  return metadata, inc

def photo2kml(files):
  tag_inds = [tag_dict[t] for t in meta_tags]
  metadata, inc = exiftool(files,tag_inds)
  # sorded by datetime
  metadata = sorted(metadata,key=lambda l:l[3])
  ndata = len(metadata)

  if not inc:
    sys.exit('Error: File not found.')
  elif not ndata:
    sys.exit('Error: GPSInfo not found in file.')

  kml_doc = KML.kml(
      KML.Document(
          KML.name(trip_name),
          KML.Style(
              KML.IconStyle(
                  KML.color(color_argb), # only valid in Google Earth
                  KML.scale(1.),         # only valid in Google Earth
                  KML.Icon(
                      KML.href(icon_url)
                  ),
                  KML.hotSpot(
                    x='0.5',
                    y='0.0',
                    xunits="fraction",
                    yunits="fraction")
              ),
              id='icon_style',
          )
      )
  )

  # append location one by one
  for meta in metadata:

    msg = 'Photo location.'
    #msg += '\nTrip: %s' % trip_name
    #msg += '\nTime: %s' % meta[3]
    #msg += '\nModel: %s' % meta[4]
    #msg += '\nName: %s' % meta[0]
    kml_doc.Document.append(
      KML.Placemark(
        # use datetime as marker name
        KML.name(meta[3]),
        KML.styleUrl('#%s' % 'icon_style'),
        KML.description(msg),
        KML.Point(KML.coordinates('%f, %f' % (meta[1],meta[2]))),
        # ExtendedData only valid in Google Map
        KML.ExtendedData(
          KML.Data(KML.value(trip_name),name='Trip'),
          KML.Data(KML.value(meta[3]),name='Time'),
          KML.Data(KML.value(meta[4]),name='Model'),
          KML.Data(KML.value(meta[0].replace('./','')),name='Name'),
        )
      )
    )
  return kml_doc, ndata

def main():
  path = './'
  if len(sys.argv) > 1:
    path = sys.argv[1] + '/'

  # get all file name in folder
  files = glob.glob(path + '*')
  kml_doc, inc = photo2kml(files)

  with open(trip_name+'.kml','w') as f:
    #print(lxml.etree.tostring(kml_doc, pretty_print=True).decode('UTF-8'))
    f.write(lxml.etree.tostring(kml_doc, pretty_print=True).decode('UTF-8'))

  print('photo2kml convertion finished: %d location(s).\n' % inc)

if __name__ == '__main__':
  main()

