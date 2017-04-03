#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import numpy as np
import os
import os.path
import stat
import glob
import sys
import getopt
import re
import argparse
import h5py
import time

__version__ = 1.1


# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "lofarFlaggedAnt.py --h5 <h5File> --ant <antFile>",
                                   description = "Reduce LOFAR single station TimerArchive data. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Maciej Serylak")
  parser.add_argument("--h5", dest = "h5File", metavar = "<h5File>", default = "", help = "specify HDF5 file with the meta info about the observation")
  parser.add_argument("--ant", dest = "antFile", metavar = "<antFile>", default = "", help = "specify text file with the meta info about the bad tiles/dipoles")
  args = parser.parse_args() # Reading command line options.

  # Start script timing.
  scriptStartTime = time.time()

  # Check for h5File and antFile presence.
  if not args.h5File and not args.antFile:
    print "\nNeed both HDF5 .h5 and _AntOff.txt files.\n"
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)

  # Loading HDF5 .h5 file.
  h5File = args.h5File
  f5 = h5py.File(h5File, 'r')
  h5BandFilter = f5.attrs['FILTER_SELECTION']
  h5Antenna = h5BandFilter.split("_")[0]
  h5Stations=f5.attrs['OBSERVATION_STATIONS_LIST']
  nCoreStations = len([s for s in h5Stations if s[0:2] == "CS"])
  # Because in the list for HBA there are sub-stations.
  if h5Antenna == "HBA":
    nCoreStations /= 2

  # Loading _AntOff.txt file
  antFile = args.antFile
  antStations, antBadTiles = np.loadtxt(antFile, usecols = [2, 3], skiprows = 0, unpack = True, dtype = str)
  index = np.zeros(len(h5Stations), dtype = int)

  # Loop through station list from h5 file and compare which were really used in observation.
  for i in range(len(h5Stations)):
    index[i] = list(antStations).index(h5Stations[i])
  newBadTiles = np.zeros(len(h5Stations))
  for i in range(len(h5Stations)):
    newBadTiles[i] = antBadTiles[index[i]]
    #print antStations[index[i]], antBadTiles[index[i]]

  print h5File.split("_")[0], nCoreStations, np.sum(newBadTiles)/(48*nCoreStations)

  # End timing script and produce result.
  scriptEndTime = time.time()
  print "\nScript running time: %.1f s.\n" % (scriptEndTime - scriptStartTime)
