#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

import math
import numpy as np
import psrchive
import optparse as opt
import sys

# Main body of the script
if __name__=="__main__":
  #
  # Parsing the command line options
  #
  usage = "Usage: %prog --ifile <input_file> --ofile <output_file>"
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width=200 # increase help width from 120 to 200
  cmdline.add_option("--ifile", dest="ifile", type="str", help="File with weights you want to clone.")
  cmdline.add_option("--ofile", dest="ofile", type="str", help="File with weights you want to overwrite.")
  cmdline.add_option("--unity", dest="unity", action="store_true", help="Replace non-zero weigths with unity.")
  cmdline.add_option("-v", "--verbose", dest="verbose", action="store_true", help="Verbose mode.")

  # reading cmd options
  (opts, args) = cmdline.parse_args()

  verbose = opts.verbose # get verbose flag
  unity = opts.unity

  if not opts.ifile and not opts.ofile:
    cmdline.print_usage()
    sys.exit(0)

  if not opts.ifile or not opts.ofile:
    print "\nNeed both files specified.\n"
    cmdline.print_usage()
    sys.exit(1)

  ifile = opts.ifile # get the stance file
  ofile = opts.ofile # get the cloned file

  if ( verbose ):
    print "Opening file %s" % (ifile)
  infile = psrchive.Archive_load(ifile)
  if ( verbose ):
    print "Opening file %s" % (ofile)
  outfile = psrchive.Archive_load(ofile)

  if ( unity ):
    print "Replacing non-zero weights with unity!"

  in_weights = infile.get_weights()
  out_weights = outfile.get_weights()

  in_subints = in_weights.shape[0]
  in_channels = in_weights.shape[1]
  out_subints = out_weights.shape[0]
  out_channels = out_weights.shape[1]

  if (in_subints != out_subints or in_channels != out_channels ):
    print "\nFiles must have the same numbers of subints and channels.\n"
    sys.exit(1)

  i = ch = 0

  for i in range(in_subints):
    in_sub = infile.get_Integration(i)
    out_sub = outfile.get_Integration(i)
    for ch in range(in_channels):
      w = in_sub.get_weight(ch)
      x = out_sub.get_weight(ch)
      if ( verbose and w != x ):
        print "Different sub = %d chan = %d infile = %f outfile = %f" %(i, ch, w, x)
      if ( unity ):
        if ( w != 0 ):
          out_sub.set_weight(ch, 1)
      else:
        out_sub.set_weight(ch, float(w))

  outfile.unload(ofile)
