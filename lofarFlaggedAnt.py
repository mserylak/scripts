#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

import numpy as np
import os, os.path, stat, glob, sys, getopt, re
import optparse as opt
import h5py

# Main body of the script
if __name__=="__main__":
  #
  # Parsing the command line options
  #
  usage = "Usage: %prog --h5 <h5_file> --ant <ant_file>"
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width=200 # increase help width from 120 to 200
  cmdline.add_option('--h5', dest='h5file', metavar='*.h5', help="HDF5 .h5 file with the meta info about the observation.", default="", type='str')
  cmdline.add_option('--ant', dest='antfile', metavar='*_AntOff.txt', help="Text file with the meta info about the bad tiles/dipoles.", default="", type='str')

  # reading cmd options
  (opts, args) = cmdline.parse_args()

  if not opts.h5file and not opts.antfile:
    cmdline.print_usage()
    sys.exit(0)

  if not opts.h5file or not opts.antfile:
    print "\nNeed both HDF5 .h5 and _AntOff.txt files.\n"
    cmdline.print_usage()
    sys.exit(1)

  # loading HDF5 .h5 file
  h5file = opts.h5file
  f5 = h5py.File(h5file, 'r')
  h5_bandFilter = f5.attrs['FILTER_SELECTION']
  h5_antenna = h5_bandFilter.split("_")[0]
  h5_stations=f5.attrs['OBSERVATION_STATIONS_LIST']
  ncorestations = len([s for s in h5_stations if s[0:2] == "CS"])
  # because in the list for HBA there are sub-stations
  if h5_antenna == "HBA":
    ncorestations /= 2

  # loading _AntOff.txt file
  antfile = opts.antfile
  ant_stations, ant_badtiles = np.loadtxt(antfile, usecols=[2, 3], skiprows=0, unpack=True, dtype=str)

  index = np.zeros(len(h5_stations))
  # loop through station list from h5 file and compare which were really used in observation
  for i in range(len(h5_stations)):
    index[i] = list(ant_stations).index(h5_stations[i])

  new_bad_tiles = np.zeros(len(h5_stations))
  for i in range(len(h5_stations)):
    new_bad_tiles[i] = ant_badtiles[index[i]]
    #print ant_stations[index[i]], ant_badtiles[index[i]]

  print h5file.split("_")[0], ncorestations, np.sum(new_bad_tiles)/(48*ncorestations)
