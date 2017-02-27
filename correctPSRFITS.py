#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import sys
import argparse
import time
import astropy.io.fits as pyfits
from astropy.time import Time

__version__ = 1.0

# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "correctPSRFITS.py --file <fileName> [options]",
                                   description = "Correct PSRFITS search data header (from bfi1 on MeerKAT). Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Maciej Serylak")
  parser.add_argument("-f", "--file", dest = "fileName", metavar = "<fileName>", default = "", help = "specify input file name")
  parser.add_argument("-r", "--ra", dest = "rightAscension", metavar = "<rightAscension>", default = "", help = "specify right ascension in HH:MM:SS.S")
  parser.add_argument("-d", "--dec", dest = "declination", metavar = "<declination>", default = "", help = "specify declination in DD:MM:SS.S")
  parser.add_argument("-e", "--ext", dest = "fileExtension", metavar = "fileExtension", default = "", help = "specify new file extension")
  parser.add_argument("-p", "--npol", dest = "nPolarisations", metavar = "nPolarisations", default = "", help = "specify number of polarisations")
  args = parser.parse_args() # Reading command line options.

  # Start script timing.
  scriptStartTime = time.time()

  # Check for fileName presence.
  if not args.fileName:
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)
  else:
    fileName = args.fileName

  # Check for rightAscension presence.
  if not args.rightAscension:
    print "Provide Right Ascension (\"HH:MM:SS.S\")"
    sys.exit(0)
  else:
    rightAscension = args.rightAscension

  # Check for declination presence.
  if not args.declination:
    print "Provide Declination (\"DD:MM:SS.S\")"
    sys.exit(0)
  else:
    declination = args.declination

  # Check for nPolarisations presence.
  if not args.nPolarisations:
    print "No polarisation given. Assuming total intensity observation."
    nPolarisations = 1
  else:
    nPolarisations = args.nPolarisations
    nPolarisations = int(nPolarisations)
    if nPolarisations != 1 and nPolarisations != 4:
      print "Wrong number of polarisation provided."
      sys.exit(0)
    if nPolarisations == 1:
      polarisationType = "AA+BB"
    elif nPolarisations == 4:
      polarisationType = "AABBCRCI"

  # Opening file and changing header parameters.
  print "Opening", fileName
  dataFile = pyfits.open(fileName, memmap=True, mode="update", save_backup=False)
  hduPrimary = dataFile[0].header
  hduHistory = dataFile[1].header
  hduSubint = dataFile[2].header
  startTime = Time(hduPrimary["STT_IMJD"] + hduPrimary["STT_SMJD"] / 3600.0 / 24.0, format = "mjd")
  startTime.format = "isot"
  startTime = startTime.value[:-3] + str(hduPrimary['STT_OFFS'])[2:]
  hduPrimary["TELESCOP"] = "MEERKAT"
  hduPrimary["FRONTEND"] = "L-BAND"
  hduPrimary["RA"] = rightAscension
  hduPrimary["DEC"] = declination
  hduPrimary["STT_CRD1"] = rightAscension
  hduPrimary["STT_CRD2"] = declination
  hduPrimary["STP_CRD1"] = rightAscension
  hduPrimary["STP_CRD2"] = declination
  hduPrimary["TRK_MODE"] = "TRACK"
  hduPrimary["OBS_MODE"] = "SEARCH"
  hduPrimary["TCYCLE"] = 0
  hduPrimary["ANT_X"] = 5109318.8410
  hduPrimary["ANT_Y"] = 2006836.3673
  hduPrimary["ANT_Z"] = -3238921.7749
  hduPrimary["NRCVR"] = 2
  hduPrimary["BACKEND"]="KAT"
  hduPrimary["CAL_MODE"] = "OFF"
  hduPrimary["CAL_FREQ"] = 0.0
  hduPrimary["CAL_DCYC"] = 0.0
  hduPrimary["CAL_PHS"] = 0.0
  hduPrimary["CAL_NPHS"]=0.0
  hduPrimary["CHAN_DM"] = 0.0
  hduPrimary["DATE-OBS"] = startTime
  hduPrimary["DATE"] = startTime
  hduSubint["NPOL"] = nPolarisations
  hduSubint["POL_TYPE"] = polarisationType
  hduSubint["NCHNOFFS"] = 0
  hduSubint["NSUBOFFS"] = 0

  # Check for fileExtension presence.
  if not args.fileExtension:
    dataFile.flush()
  else:
    fileExtension = args.fileExtension
    saveFilename = fileName + "." + fileExtension
    dataFile.writeto(saveFilename)
