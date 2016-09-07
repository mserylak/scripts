#!/usr/bin/env python

# Copyright (C) 2016 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform receipients that you have modified the original work.

import numpy as np
import os
import sys
import struct
import ephem
import datetime
import optparse as opt

# Functions used in SIGPROC header creation
def _write_string(key, value):
  return "".join([struct.pack("I", len(key)), key, struct.pack("I", len(value)), value])

def _write_int(key, value):
  return "".join([struct.pack("I",len(key)), key, struct.pack("I", value)])

def _write_double(key, value):
  return "".join([struct.pack("I",len(key)), key, struct.pack("d", value)])

def _write_char(key, value):
  return "".join([struct.pack("I",len(key)), key, struct.pack("b", value)])

# Main body of the script
if __name__=="__main__":
  # Parsing the command line options
  usage = "Usage: %prog --tsamp=655.36 --tstart=\"1459453729.12345\" --raw=\"input.dada\" --out=\"output.fil\""
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 100 # Increase space reserved for option flags (default 24), trick to make the help more readable.
  cmdline.formatter.width = 250 # Increase help width from 120 to 200.
  cmdline.add_option("--tsamp", type = "float", dest = "samplingTime", metavar = "<samplingTime>", default = "655.36" , help = "Give sampling time in microseconds.")
  cmdline.add_option("--tstart", type = "float", dest = "unixTime", metavar = "<unixTime>", default = "1459453729.12345" , help = "Give UTC start time of observation in Unix time.")
  cmdline.add_option("--source", type = "string", dest = "sourceName", metavar = "<sourceName>", default = "J0835-4510", help = "Give source name.")
  cmdline.add_option("--ra", type = "string", dest = "rightAscension", metavar = "<rightAscension>", default = "08:35:20.61149", help = "Give right ascension of the source.")
  cmdline.add_option("--dec", type = "string", dest = "declination", metavar = "<declination>", default = "-45:10:34.8751", help = "Give declination of the source.")
  cmdline.add_option("--raw", type = "string", dest = "dadaFile", metavar = "<dadaFile>", help = "Give input filename.")
  cmdline.add_option("--out", type = "string", dest = "outFileName", metavar = "<outFileName>", default = "out.fil", help = "Give output filename.")
  (opts, args) = cmdline.parse_args() # Reading command line options.
  if not opts.dadaFile:
    cmdline.print_usage()
    sys.exit(0)
  outFileName = opts.outFileName
  #print outFileName
  dadaFile = opts.dadaFile
  #print dadaFile
  samplingTime = opts.samplingTime
  samplingTime = samplingTime * 1e-6 # Turn to microseconds.
  #print samplingTime
  unixTime = opts.unixTime
  #print unixTime
  decimalUnixTime = (str(unixTime - int(unixTime)))[1:]
  intUnixTime = int(unixTime)
  unixDateTime = datetime.datetime.fromtimestamp(intUnixTime).strftime("%Y-%m-%d %H:%M:%S")
  unixDateTime = unixDateTime + decimalUnixTime
  startTimeMJD = ephem.julian_date(ephem.Date(unixDateTime))-2400000.5 # convert to MJD
  #print startTimeMJD
  sourceName = opts.sourceName
  #print sourceName
  rightAscension = opts.rightAscension
  #print rightAscension
  declination = opts.declination
  #print declination
  numberChannels = 1024
  #print numberChannels
  numberPseudoStokes = 4
  #print numberPseudoStokes
  numberBytesPerSample = 2
  #print numberBytesPerSample
  fileSize = os.stat(dadaFile).st_size
  #print fileSize
  spectraNumber = fileSize / (numberChannels * numberBytesPerSample * numberPseudoStokes)
  #print spectraNumber
  blockSize = int(numberChannels * numberBytesPerSample * numberPseudoStokes)
  #print blockSize
  numberOfItems = blockSize / 2
  #print numberOfItems
  fileOut = open(outFileName, "ab+")
  headerStart = "HEADER_START"
  headerEnd = "HEADER_END"
  header = "".join([struct.pack("I", len(headerStart)), headerStart])
  header = "".join([header, _write_string("source_name", sourceName)])
  header = "".join([header, _write_int("machine_id", 13)])
  header = "".join([header, _write_int("telescope_id", 64)])
  src_raj = float(rightAscension.replace(":", ""))
  header = "".join([header, _write_double("src_raj", src_raj)])
  src_dej = float(declination.replace(":", ""))
  header = "".join([header, _write_double("src_dej", src_dej)])
  header = "".join([header, _write_int("data_type", 1)])
  header = "".join([header, _write_double("fch1", 2021.6093750)])
  header = "".join([header, _write_double("foff", -0.390625)])
  header = "".join([header, _write_int("nchans", numberChannels)])
  header = "".join([header, _write_int("nbits", 32)])
  header = "".join([header, _write_double("tstart", startTimeMJD)])
  header = "".join([header, _write_double("tsamp", samplingTime)])
  header = "".join([header, _write_int("nifs", 1)])
  header = "".join([header, struct.pack("I", len(headerEnd)), headerEnd])
  fileOut.write(header)
  fileIn = open(dadaFile, "rb")
  for spectrum in range(int(spectraNumber)):
    fileIn.seek(blockSize * spectrum, os.SEEK_SET)
    dadaArray = np.fromfile(fileIn, dtype = np.int16, count = numberOfItems)
    xxArray = dadaArray[::4] # get every 4th element of the array
    yyArray = dadaArray[1::4] # get every 5th element of the array
    xxArrayFloat32 = xxArray.astype(dtype = np.float32)
    yyArrayFloat32 = yyArray.astype(dtype = np.float32)
    stokesI = xxArrayFloat32 + yyArrayFloat32
    #stokesI[0:256] = 0.0
    #stokesI[768:1024] = 0.0
    bytesStokesI = stokesI.tobytes(order = "C")
    fileOut.seek(0, 2) # Move pointer to the end of file.
    fileOut.write(bytesStokesI)
  fileOut.close()
