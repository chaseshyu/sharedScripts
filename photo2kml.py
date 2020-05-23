#!/usr/bin/env python3
#-*- coding: utf-8 -*-
#  photo2kml.py
#  convert photo's metadata to kml for mapping.
#
#  Created by Chase J. Shyu on May 23rd, 2020.
# Environment dependency:
#   exiftool, python-pykml
import os, time, subprocess
import numpy as np
from pykml.factory import KML_ElementMaker as KML
from lxml import etree

trip_name = "Good Trip 2020"

def main():
  cmd = 'exiftool -c \'%.7f\' -GPSPosition -csv -datetimeoriginal -Model .'
  metadata,_ = execute(cmd)
  metadata = metadata.decode('UTF-8').split('\n')[1:-1]
  time_list = [time.strptime(m.split(',')[3], "%Y:%m:%d %H:%M:%S") for m in metadata]
  sort_index = sorted(range(len(time_list)), key=lambda k: time_list[k])

  fld = KML.Folder(KML.name(trip_name))

  for i in sort_index:
    meta = metadata[i].split(',')
    meta[0] = meta[0][2:]
    meta[1] = meta[1].replace('"', "").replace('\'', "")
    meta[2] = meta[2].replace('"', "").replace('\'', "")

    fld.append(
      KML.Placemark(
        KML.name(meta[3]),
        KML.description('Photo location'),
        KML.Point(KML.coordinates(meta[2]+', '+meta[1])),
        KML.ExtendedData(
          KML.Data(KML.value(trip_name),name='Trip'),
          KML.Data(KML.value(meta[3]),name='Time'),
          KML.Data(KML.value(meta[4]),name='Model'),
          KML.Data(KML.value(meta[0]),name='Name')
        ) 
      )
    )

  with open(trip_name+'.kml','w') as f:
    #print(etree.tostring(fld, pretty_print=True).decode('UTF-8'))
    f.write(etree.tostring(fld, pretty_print=True).decode('UTF-8'))

def execute(cmd):
  cmd = cmd.split(" ")
  p = subprocess.Popen(cmd, stdout=subprocess.PIPE, 
                            stderr=subprocess.PIPE)
  out, err = p.communicate()
  return out, err

if __name__ == '__main__':
  main()

