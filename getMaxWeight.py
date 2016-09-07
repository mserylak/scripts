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
import os, os.path, stat, glob, sys, getopt, re
import optparse as opt

np.set_printoptions(threshold='nan') # print entire lists/arrays without truncation

# Main body of the script
if __name__=="__main__":
  # Parsing the command line options
  usage = "Usage: %prog --file <ar file>"
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width=200 # increase help width from 120 to 200
  cmdline.add_option('--file', dest='ar_file', metavar='*.ar', help="State the name of the file to be analysed.", default="", type='str')
  cmdline.add_option('--verbose', dest='verbose', action="store_true", help="Verbose mode - reports zero weights for each subint.")

  # reading cmd options
  (opts, args) = cmdline.parse_args()

  if not opts.ar_file:
    print "\nNeed file to analyse!\n"
    cmdline.print_usage()
    sys.exit(1)

  verbose = opts.verbose
  arch = psrchive.Archive_load(opts.ar_file) # arch object
  weights = arch.get_weights() # get_weights() method to read weigths into the file
  weights.size # just a control statement to get the size of array (number of cells)
  subints = weights.shape[0]
  channels = weights.shape[1]
  max_weight = np.max(weights)
  if ( verbose ):
    print "File %s has %s subints and %s channels with maximum weitght %s" % (opts.ar_file, subints, channels, max_weight)
  else:
    print "%s nsubint=%s nchan=%s max_weight=%s" % (opts.ar_file, subints, channels, max_weight)
