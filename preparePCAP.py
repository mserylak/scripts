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
  # Defining global variables.
  pcapGlobalHeader = 24 # Pcap files starts with 24 byte header.
  pcapHeader = 58 # Each packet in pcap file has 58 byte header.
  packetSize = 8208 # Size of each packet.
  spectraPerSecond = 390625
  numberChannels = 1024
  numberPseudoStokes = 4
  numberOfItems = numberPseudoStokes * numberChannels
  # Parsing the command line options
  usage = "Usage: %prog --tsamp=2.56 --tstart=\"1459453729.12345\" --raw=\"input.dat\" --out=\"output.fil\""
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 100 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width = 250 # increase help width from 120 to 200
  cmdline.add_option("--source", type = "string", dest = "sourceName", metavar = "<sourceName>", default = "J0835-4510", help = "Give source name.")
  cmdline.add_option("--ra", type = "string", dest = "rightAscension", metavar = "<rightAscension>", default = "08:35:20.61149", help = "Give right ascension of the source.")
  cmdline.add_option("--dec", type = "string", dest = "declination", metavar = "<declination>", default = "-45:10:34.8751", help = "Give declination of the source.")
  cmdline.add_option('--raw', type = 'string', dest = 'pcapFile', metavar = '<pcapFile>', help = 'Give input filename.')
  cmdline.add_option('--out', type = 'string', dest = 'outFileName', metavar = '<outFileName>', default = 'out.fil', help = 'Give output filename.')
  cmdline.add_option("--pad", dest = "zeroPad", action = "store_true", default = False, help = "Pad missing packets with zeros.")
  (opts, args) = cmdline.parse_args() # reading cmd options
  if not opts.pcapFile:
    cmdline.print_usage()
    sys.exit(0)
  outFileName = opts.outFileName
  #print outFileName
  zeroPad = opts.zeroPad
  pcapFile = opts.pcapFile
  #print pcapFile
  fileSize = os.stat(pcapFile).st_size
  #print fileSize
  spectraNumber = (fileSize - pcapGlobalHeader) / (packetSize + pcapHeader)
  #print spectraNumber
  fileIn = open(pcapFile, "rb")
  fileIn.seek(pcapGlobalHeader + pcapHeader)
  UTCtimestamp = np.fromfile(fileIn, dtype = np.uint64, count = 1)[0]
  accumulationNumber = np.fromfile(fileIn, dtype = np.uint32, count = 1)[0]
  accumulationRate = np.fromfile(fileIn, dtype = np.uint32, count = 1)[0]
  #print UTCtimestamp, accumulationNumber, accumulationRate
  derivedUTCtimestamp = UTCtimestamp
  derivedAccumulationNumber = accumulationNumber
  fileIn.close()
  unixDateTime = datetime.datetime.fromtimestamp(int(UTCtimestamp)).strftime("%Y-%m-%d %H:%M:%S")
  decimalUnixTime = str(float(accumulationNumber) / float(spectraPerSecond))
  unixDateTime = unixDateTime + decimalUnixTime
  startTimeMJD = ephem.julian_date(ephem.Date(unixDateTime)) - 2400000.5 # convert to MJD
  #print startTimeMJD
  samplingTime = accumulationRate * 2.56 * 1e-6 # Turn to microseconds.
  #print samplingTime
  sourceName = opts.sourceName
  #print sourceName
  rightAscension = opts.rightAscension
  #print rightAscension
  declination = opts.declination
  #print declination
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
  counter = 0
  fileIn = open(pcapFile, "rb")
  fileIn.seek(pcapGlobalHeader)
  fileIn.seek(pcapHeader)
  while True:
    try:
      if counter == 0:
        fileIn.seek(pcapGlobalHeader + pcapHeader)
      elif counter != 0:
        fileIn.seek(pcapGlobalHeader + ((counter + 1) * pcapHeader) + (counter * packetSize))
      UTCtimestamp = np.fromfile(fileIn, dtype = np.uint64, count = 1)[0]
      accumulationNumber = np.fromfile(fileIn, dtype = np.uint32, count = 1)[0]
      accumulationRate = np.fromfile(fileIn, dtype = np.uint32, count = 1)[0]
      #print UTCtimestamp, accumulationNumber, accumulationRate
      if (derivedAccumulationNumber >= spectraPerSecond):
        derivedAccumulationNumber = derivedAccumulationNumber % spectraPerSecond
        derivedUTCtimestamp = derivedUTCtimestamp + 1
      #print UTCtimestamp, accumulationNumber, accumulationRate, derivedUTCtimestamp, derivedAccumulationNumber, accumulationRate
      if derivedAccumulationNumber != accumulationNumber:
        print "MISSING PACKET:", derivedUTCtimestamp, derivedAccumulationNumber, accumulationRate
        derivedAccumulationNumber = derivedAccumulationNumber + accumulationRate
        if zeroPad:
          stokesI = np.zeros(numberChannels)
          bytesStokesI = stokesI.tobytes(order = "C")
          fileOut.seek(0, 2)
          fileOut.write(bytesStokesI)
      else:
        dataArray = np.fromfile(fileIn, dtype = np.int16, count = numberOfItems)
        xxArray = dataArray[::4] # get every 4th element of the array
        yyArray = dataArray[1::4] # get every 5th element of the array
        xxArrayFloat32 = xxArray.astype(dtype = np.float32)
        yyArrayFloat32 = yyArray.astype(dtype = np.float32)
        stokesI = xxArrayFloat32 + yyArrayFloat32
        bytesStokesI = stokesI.tobytes(order = "C")
        fileOut.seek(0, 2)
        fileOut.write(bytesStokesI) 
      derivedAccumulationNumber = derivedAccumulationNumber + accumulationRate
      counter = counter + 1
    except IndexError:
      print "End of file reached!"
      fileOut.close()
      sys.exit(0)
