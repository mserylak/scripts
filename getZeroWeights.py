#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import argparse
import numpy as np
import psrchive


__version__ = 1.1

np.set_printoptions(threshold='nan') # print entire lists/arrays without truncation


# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(prog = "getZeroWeights",
                                   usage = "%(prog)s [options]",
                                   description = "Get the number of subint-channels with zero weigths (i.e. cleaned) from TimerArchive/PSRFITS file. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Maciej Serylak")
  parser.add_argument("-v", "--verbose", dest = "verbose", action = "store_true", help = "verbose mode - reports zero weights for each subint")
  parser.add_argument("-p", "--psrsh", dest = "psrsh", action = "store_true", help = "write commands to psrsh script file")
  parser.add_argument("-f", "--file", dest = "file", default = None, help = "name of the file to be analysed")
  args = parser.parse_args() # reading command line options.
  file = args.file # getting the filename
  verbose = args.verbose # getting verbose flag
  psrsh = args.psrsh # getting psrsh flag
  if verbose:
    print "Opening file %s" % file
  arch = psrchive.Archive_load(file) # file is read and loaded into object
  weights = arch.get_weights() # get_weights() reads weights from object
  subints = weights.shape[0]
  channels = weights.shape[1]
  if verbose:
    print "File %s has %s subints and %s channels." % (file, subints, channels)
  else:
    print "%s nsubint=%s nchan=%s" % (file, subints, channels)
  if psrsh:
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
    if verbose:
      percent_sub = (float(spectrum)/float(channels))*100
      print "Subint %s has %s channels (%.2f%%) set to zero. %s" % (i, spectrum, percent_sub, empty_channels)
    if psrsh:
      for k in range(len(empty_channels)): # get the lengths of list with zero-weights channels for every sub-integration
        #print "zap such %d,%d" % (i, empty_channels[k])
        np.savetxt(psrsh_file, np.c_[i, empty_channels[k]], fmt='zap such %d,%d')
  percentage = (float(counter)/float(weights.size))*100
  print "%s data points out of %s with weights set to zero." % (counter, weights.size)
  print "%.2f%% data points set to zero." % (percentage)
