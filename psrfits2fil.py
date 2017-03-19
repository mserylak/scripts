#!/usr/bin/env python

# Copyright (C) 2017 by Paul Scholz, Patrick Lazarus, Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import numpy as np
import psrfits
import filterbank
import sigproc
import argparse
import sys
import os
import time

__version__ = 1.2


def translateHeader(psrfitsFile):
  psrfitsHeader = psrfitsFile.header
  subintHdr = psrfitsFile.fits["SUBINT"].header
  subintData = psrfitsFile.fits["SUBINT"].data
  filHeader = {}
  if psrfitsHeader["TELESCOP"] in sigproc.telescope_ids:
    filHeader["telescope_id"] = sigproc.telescope_ids[psrfitsHeader["TELESCOP"]]
  else:
    filHeader["telescope_id"] = -1
  if psrfitsHeader["BACKEND"] in sigproc.machine_ids:
    filHeader["machine_id"] = sigproc.machine_ids[psrfitsHeader["BACKEND"]]
  else:
    filHeader["machine_id"] = -1
  filHeader["data_type"] = 1
  filHeader["rawdatafile"] = os.path.basename(psrfitsFile.filename)
  filHeader["source_name"] = psrfitsHeader["SRC_NAME"]
  filHeader["src_raj"] = float(psrfitsHeader["RA"].replace(":",""))
  filHeader["src_dej"] = float(psrfitsHeader["DEC"].replace(":",""))
  filHeader["tstart"] = psrfitsHeader["STT_IMJD"] + ((psrfitsHeader["STT_SMJD"] + psrfitsHeader["STT_OFFS"]) / 86400.0)
  filHeader["tsamp"] = subintHdr["TBIN"]
  filHeader["nbits"] = None
  filHeader["fch1"] = psrfitsHeader["OBSFREQ"] + np.abs(psrfitsHeader["OBSBW"]) / 2.0 - np.abs(subintHdr["CHAN_BW"]) / 2.0
  filHeader["foff"] = -1.0 * np.abs(subintHdr["CHAN_BW"])
  filHeader["nchans"] = subintHdr["NCHAN"]
  filHeader["nifs"] = subintHdr["NPOL"]
  return filHeader


def main(fitsFileName, outFile, nBits, applyWeights, applyScales, applyOffsets):
  # Start script timing.
  scriptStartTime = time.time()

  psrfitsFile = psrfits.PsrfitsFile(fitsFileName)
  filHeader = translateHeader(psrfitsFile) 
  filHeader["nbits"] = nBits
  outfil = filterbank.create_filterbank_file(outFile, filHeader, nbits = nBits)

  # Flip the band if frequency channels are in ascending order.
  if psrfitsFile.fits["SUBINT"].header["CHAN_BW"] > 0:
    flipBand = True
    print "\nFits file frequencies in ascending order. Flipping the frequency band.\n"
  else:
    flipBand = False

  # Check input data for nBits.
  if psrfitsFile.nbits < 4:
    raise ValueError("\n%d-bit data not supported.\n" % psrfitsFile.nbits)

  # Calculate scaling factor if output data is not 32 bits.
  if nBits != 32:
    print "\nCalculating statistics on first subintegration.\n"
    subint0 = psrfitsFile.read_subint(0, applyWeights, applyScales, applyOffsets)
    #newMax = np.mean(subint0) + 3 * np.std(subint0)
    newMax = 3 * np.median(subint0)
    print "\n3 * median = %f\n" % newMax
    if newMax > 2.0**nBits:
      scaleFlag = True
      scaleFactor = newMax / ( 2.0**nBits )
      print "\nScaling data by %f.\n" % (1 / scaleFactor)
      print "\nValues larger than %f (pre-scaling) will be set to %f.\n" % (newMax, 2.0**nBits - 1)
    else:
      scaleFlag = False
      scaleFactor = 1
      print "\nNo scaling necessary.\n"
  else:
      scaleFactor = 1
      print "\nNo scaling necessary for 32-bit float output file.\n"

  print "\nWriting data...\n"
  sys.stdout.flush()
  oldPercentCounter = ""

  # Convert the data to filterbank.
  for iSub in range(int(psrfitsFile.nsubints)):
    subint = psrfitsFile.read_subint(iSub, applyWeights, applyScales, applyOffsets)
    if flipBand:
      subint = np.fliplr(subint)
    subint /= scaleFactor
    outfil.append_spectra(subint)
    percentCounter = "%d" % (isub*100.0/psrfitsFile.nsubints)
    if percentCounter != oldPercentCounter:
      sys.stdout.write("% 4s%% complete\r" % pcnt)
      sys.stdout.flush()

  print "\nDone.\n"
  outfil.close()

  # End timing script and produce result.
  scriptEndTime = time.time()
  print "\nScript running time: %.1f s.\n" % (scriptEndTime - scriptStartTime)

# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "psrfits2fil.py [options] --file <inputFits> ",
                                   description = "Convert PSRFITS data into SIGPROC filterbank data file. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Paul Scholz, Patrick Lazarus, Maciej Serylak")
  parser.add_argument("--file", dest = "fitsFileName", action = "store", metavar = "<fileName>", default = "", help = "specify input file name")
  parser.add_argument("--nBit", dest = "nBits", action = "store", metavar = "<nBits>", default = 8, type = int, help = "specify number of bits in the output .fil file (default: 8)")
  parser.add_argument("--out", dest = "outFile", action = "store", metavar = "<outFile>", default = "", help = "specify output filterbank file name (default: replace input extension with .fil)")
  parser.add_argument("--noweights", dest = "applyWeights", action = "store_true", default = True, help = "do not apply weights when converting data")
  parser.add_argument("--noscales",  dest = "applyScales",  action = "store_true", default = True, help = "do not apply scales when converting data")
  parser.add_argument("--nooffsets", dest = "applyOffsets", action = "store_true", default = True, help = "do not apply offsets when converting data")
  args = parser.parse_args() # Reading command line options.

  # Check for fitsFileName presence.
  if not args.fitsFileName:
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)
  else:
    fitsFileName = args.fitsFileName

  # Check for outFile presence.
  if args.outFile:
    outFile = args.outFile
  else:
    outFile = '.'.join(fitsFileName.split('.')[:-1]) + '.fil'

  # Execute main block of the script.
  main(fitsFileName, outFile, args.nBits, args.applyWeights, args.applyScales, args.applyOffsets)
