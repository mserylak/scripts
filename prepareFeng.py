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
  # Parsing the command line options.
  usage = "Usage: %prog --tsamp=2.56 --tstart=\"1459453729.12345\" --raw=\"input.dat\" --out=\"output.fil\""
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 100 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width = 250 # increase help width from 120 to 200
  cmdline.add_option('--tsamp', type = 'float', dest = 'samplingTime', metavar = '<samplingTime>', default = '2.56' , help = 'Give sampling time in microseconds.')
  cmdline.add_option('--tstart', type = 'float', dest = 'unixTime', metavar = '<unixTime>', default = '1459453729.12345' , help = 'Give UTC start time of observation in Unix time.')
  cmdline.add_option("--source", type = "string", dest = "sourceName", metavar = "<sourceName>", default = "J0835-4510", help = "Give source name.")
  cmdline.add_option("--ra", type = "string", dest = "rightAscension", metavar = "<rightAscension>", default = "08:35:20.61149", help = "Give right ascension of the source.")
  cmdline.add_option("--dec", type = "string", dest = "declination", metavar = "<declination>", default = "-45:10:34.8751", help = "Give declination of the source.")
  cmdline.add_option('--raw', type = 'string', dest = 'f_engineFile', metavar = '<f_engineFile>', help = 'Give input filename.')
  cmdline.add_option('--out', type = 'string', dest = 'outFileName', metavar = '<outFileName>', default = 'out.fil', help = 'Give output filename.')
  (opts, args) = cmdline.parse_args() # reading cmd options
  if not opts.f_engineFile:
    cmdline.print_usage()
    sys.exit(0)
  outFileName = opts.outFileName
  #print outFileName
  f_engineFile = opts.f_engineFile
  #print f_engineFile
  samplingTime = opts.samplingTime
  samplingTime = samplingTime * 10e-7 # Turn to microseconds.
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
  numberRawPolarizations = 2
  #print numberRawPolarizations
  numberBytesPerSample = 1
  #print numberBytesPerSample
  fileSize = os.stat(f_engineFile).st_size
  #print fileSize
  spectraNumber = fileSize / (numberChannels * numberBytesPerSample * numberRawPolarizations)
  #print spectraNumber
  blockSize = int(numberChannels * numberBytesPerSample * numberRawPolarizations)
  #print blockSize
  numberOfItems = blockSize
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
  fileIn = open(f_engineFile, "rb")
  fileOut = open(outFileName, "ab+")
  for spectrum in range(int(spectraNumber)):
    fileIn.seek(blockSize * spectrum, os.SEEK_SET)
    binaryDataArray = np.fromfile(fileIn, dtype = np.uint8, count = numberOfItems)
    realDataArray = np.bitwise_and(binaryDataArray, 0x0f)
    #imagDataArray = np.bitwise_and(binaryDataArray >> 4, 0x0f)
    evenChanPol0 = realDataArray[::4]
    evenChanPol1 = realDataArray[2::4]
    oddChanPol0 = realDataArray[1::4]
    oddChanPol1 = realDataArray[3::4]
    xPol = np.empty((evenChanPol0.size + evenChanPol0.size), dtype = evenChanPol0.dtype)
    xPol[0::2] = evenChanPol0
    xPol[1::2] = evenChanPol0
    yPol = np.empty((evenChanPol1.size + evenChanPol1.size), dtype = evenChanPol1.dtype)
    yPol[0::2] = evenChanPol1
    yPol[1::2] = evenChanPol1
    xPolFloat32 = xPol.astype(dtype = np.float32)
    yPolFloat32 = yPol.astype(dtype = np.float32)
    totalIntensity = (xPolFloat32 * xPolFloat32) + (yPolFloat32 * yPolFloat32)
    bytesTotalIntensity = totalIntensity.tobytes(order = "C")
    fileOut.seek(0, 2) # Move pointer to the end of file.
    fileOut.write(bytesTotalIntensity)
  fileOut.close()
