#!/usr/bin/env python

# Copyright (C) 2016 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

import math
import numpy as np
import psrchive
import matplotlib.pylab as plt
import sys
from optparse import OptionParser

np.set_printoptions(threshold='nan') # print entire lists/arrays without truncation
parser = OptionParser(usage="%prog <options>", description="Find the peak of polarization-, time-, frequency-scrunched and dedispersed profile from TimerArchive/PSRFITS file.")
parser.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
parser.formatter.width=200 # increase help width from 120 to 200
parser.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode - reports zero weights for each subint.")
parser.add_option("-p", "--plot", dest="plot", action="store_true", help="Plot profile.")
parser.add_option("-n", "--nwin", type="int", dest="nwin", help="State the number of bins to use for window width search, e.g. --nwin \"nwinparam\"")
parser.add_option("-f", "--file", type="string", help="State the name of the file to be analysed, e.g. --file \"fileparam\"")
(options, args) = parser.parse_args()
file = options.file # get the file
verbose = options.verbose # get verbose flag
plot = options.plot
nwin = options.nwin
if not options.file:
  parser.print_usage()
  sys.exit(0)
if verbose:
  print "Opening file %s" % (file)
archive = psrchive.Archive_load(file) # arch object is loaded into the file into arch
if verbose:
  print "Preparing average profile..."
archive.tscrunch()
archive.pscrunch()
archive.dedisperse()
archive.fscrunch()
archive.remove_baseline()
profileRMS = archive.rms_baseline()
#print "profileRMS", profileRMS
profile = archive.get_Profile(0,0,0)
profileData = profile.get_amps()
maxBin = profile.find_max_bin()
#print "maxBin", maxBin
tolerance = 2 * profileRMS
#print "tolerance", tolerance
leftNwinBoundary = maxBin - nwin
if leftNwinBoundary < 0:
  leftNwinBoundary
#print "leftNwinBoundary", leftNwinBoundary
rightNwinBoundary = maxBin + nwin
if rightNwinBoundary > 1024:
  rightNwinBoundary = 1024
#print "rightNwinBoundary", rightNwinBoundary
for n in range(maxBin, leftNwinBoundary, -1):
  Intensity = profileData[n]
  if (Intensity <= tolerance):
    IntensityLeftOnpulse = Intensity
    binOnpulseLeft = n
    break
for n in range(maxBin, rightNwinBoundary, 1):
  Intensity = profileData[n]
  if (Intensity <= tolerance or n == rightNwinBoundary - 1):
    IntensityRightOnpulse = Intensity
    binOnpulseRight = n
    break
print "File %s has a peak at bin %d/pulse phase %f and pulse boundaries between bins %d and %d/pulse phases %f and %f." % (file, maxBin, (maxBin / 1024.0), binOnpulseLeft, binOnpulseRight, (binOnpulseLeft / 1024.0), (binOnpulseRight / 1024.0))
if plot:
  plt.plot(profileData, 'b-')
  plt.show()
