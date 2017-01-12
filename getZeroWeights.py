#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import math
import numpy as np
import psrchive
from optparse import OptionParser

np.set_printoptions(threshold='nan') # print entire lists/arrays without truncation

# Initialise parameters.
parser = OptionParser(usage="%prog <options>", description="Get the number of subint-channels with zero weigths (i.e. cleaned) from TimerArchive/PSRFITS file.")
parser.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
parser.formatter.width=200 # increase help width from 120 to 200
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode - reports zero weights for each subint.")
parser.add_option("-p", "--psrsh", dest="psrsh", action="store_true", help="Write commands to psrsh script file.")
parser.add_option("-f", "--file", type="string", dest="file", default="B1508+55_L236566_SAP0_BEAM0.ar.cg", help="State the name of the file to be analysed, e.g. --file \"fileparam\"")
parser.add_option("-w", "--weight", type="string", dest="weight", )

(options, args) = parser.parse_args()
file = options.file # get the file
verbose = options.verbose # get verbose flag
psrsh = options.psrsh # get psrsh flag
if ( verbose ):
  print "Opening file %s" % (file)
arch = psrchive.Archive_load(file) # arch object is loaded into the file into arch
weights = arch.get_weights() # get_weights() method to read weigths into the file
weights.size # just a control statement to get the size of array (number of cells)
subints = weights.shape[0]
channels = weights.shape[1]
if ( verbose ):
  print "File %s has %s subints and %s channels." % (file, subints, channels)
else:
  print "%s nsubint=%s nchan=%s" % (file, subints, channels)
if ( psrsh ):
  filename_psrsh = file + ".psh"
  psrsh_file = open(filename_psrsh, "w")
  psrsh_file.write("#!/usr/bin/env psrsh\n\n")
  psrsh_file.write("# Run with psrsh -e <ext> <script>.psh <archive>.ar\n\n")
i = j = counter = spectrum = 0 # zeroing the counters
empty_channels = [i for i in range(channels)]
for i in range(subints):
  spectrum = 0
  del empty_channels[:]
  for j in range(channels):
    if weights[i][j] == 0.0:
      counter += 1
      spectrum += 1
      empty_channels.append(j)
  if ( verbose ):
    percent_sub = (float(spectrum)/float(channels))*100
    print "Subint %s has %s channels (%.2f%%) set to zero. %s" % (i, spectrum, percent_sub, empty_channels)
  if ( psrsh ):
    for k in range(len(empty_channels)): # get the lenghts of list with zero-weights channels for every subintegration?
      #print "zap such %d,%d" % (i, empty_channels[k])
      np.savetxt(psrsh_file, np.c_[i, empty_channels[k]], fmt='zap such %d,%d')
percentage = (float(counter)/float(weights.size))*100
print "%s data points out of %s with weights set to zero." % (counter, weights.size)
print "%.2f%% data points set to zero." % (percentage)
