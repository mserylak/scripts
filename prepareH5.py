#!/usr/bin/env python

# Copyright (C) 2016 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import numpy as np
import h5py
import os
import struct
import sys
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
  # Defining global options and variables.
  np.set_printoptions(threshold=np.nan)
  samplingClock = 1712.0e6
  print ("samplingClock: %.f Hz") % samplingClock
  complexChannels = 8192.0
  print ("complexChannels: %f") % complexChannels
  channelBW = (samplingClock / complexChannels) * 1e-6
  print ("channelBW: %.10f MHz") % channelBW

  # Parsing the command line options
  usage = "Usage: %prog --raw0=\"input_pol0.h5\" --raw1=\"input_pol1.h5\" --out=\"output.fil\""
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 100 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width = 250 # increase help width from 120 to 200
  cmdline.add_option("--freq", type = "float", dest = "freqCent", metavar = "<freqCent>", default = "1391.0" , help = "Give centre frequency.")
  cmdline.add_option("--chunk", type = "int", dest = "chunkSize", metavar = "<chunkSize>", default = "256" , help = "Give number of samples for script to proccess.")
  cmdline.add_option("--ndec", type = "int", dest = "decimationFactor", metavar = "<decimationFactor>", default = "1" , help = "Give decimation factor.")
  cmdline.add_option("--source", type = "string", dest = "sourceName", metavar = "<sourceName>", default = "J0835-4510", help = "Give source name.")
  cmdline.add_option("--ra", type = "string", dest = "rightAscension", metavar = "<rightAscension>", default = "08:35:20.61149", help = "Give right ascension of the source.")
  cmdline.add_option("--dec", type = "string", dest = "declination", metavar = "<declination>", default = "-45:10:34.8751", help = "Give declination of the source.")
  cmdline.add_option("--raw0", type = "string", dest = "h5FilePol0", metavar = "<h5FilePol0>", help = "Give input pol0 filename.")
  cmdline.add_option("--raw1", type = "string", dest = "h5FilePol1", metavar = "<h5FilePol1>", help = "Give input pol1 filename.")
  cmdline.add_option("--out", type = "string", dest = "outFileName", metavar = "<outFileName>", default = "out.fil", help = "Give output filename.")
  cmdline.add_option("--pol", dest="fullStokes", action="store_true", help="Convert to full Stokes.")
  (opts, args) = cmdline.parse_args() # reading cmd options
  if not opts.h5FilePol0 or not opts.h5FilePol1:
    cmdline.print_usage()
    sys.exit(0)

  # Getting boolean options.
  fullStokes = opts.fullStokes
  print ("fullStokes: %s") % (fullStokes)

  # Loading the files.
  h5FilePol0 = opts.h5FilePol0
  h5FilePol1 = opts.h5FilePol1
  print ("h5FilePol0: %s") % h5FilePol0
  print ("h5FilePol1: %s") % h5FilePol1
  dataH5FilePol0 = h5py.File(h5FilePol0, "r")
  dataH5FilePol1 = h5py.File(h5FilePol1, "r")

  # Getting number of channels from each file.
  channelNumberPol0 = dataH5FilePol0["Data/bf_raw"].shape[0]
  channelNumberPol1 = dataH5FilePol1["Data/bf_raw"].shape[0]
  print ("channelNumberPol0: %d") % channelNumberPol0
  print ("channelNumberPol1: %d") % channelNumberPol1

  # Checking if number of channels is the same in each file.
  if (channelNumberPol0 != channelNumberPol1):
    print ("Number of channels differs between the polarizations.")
    print ("channelNumberPol0 %d != channelNumberPol1 %d") % (channelNumberPol0, channelNumberPol1)
    sys.exit(0)

  # Getting number of spectra from each file.
  spectraNumberPol0 = dataH5FilePol0["Data/bf_raw"].shape[1]
  spectraNumberPol1 = dataH5FilePol1["Data/bf_raw"].shape[1]
  print ("spectraNumberPol0: %d") % spectraNumberPol0
  print ("spectraNumberPol1: %d") % spectraNumberPol1

  # Getting ADC counts from each file.
  countADCPol0 = dataH5FilePol0["Data/timestamps"][:]
  countADCPol1 = dataH5FilePol1["Data/timestamps"][:]
  print ("countADCPol0[0]: %d") % countADCPol0[0]
  print ("countADCPol1[0]: %d") % countADCPol1[0]

  # Calculating where both files start overlaping.
  if (countADCPol0[0] > countADCPol1[0]):
    startSyncADC = countADCPol0[0]
    startIndexPol1 = np.where(countADCPol1 == startSyncADC)[0][0]
    startIndexPol0 = 0
    print ("startIndexPol0: %d") % startIndexPol0
    print ("startIndexPol1: %d") % startIndexPol1
  elif (countADCPol0[0] < countADCPol1[0]):
    startSyncADC = countADCPol1[0]
    startIndexPol0 = np.where(countADCPol0 == startSyncADC)[0][0]
    startIndexPol1 = 0
    print ("startIndexPol0: %d") % startIndexPol0
    print ("startIndexPol1: %d") % startIndexPol1
  else:
    startSyncADC = countADCPol0[0]
    startIndexPol0 = 0
    startIndexPol1 = 0
    print ("startIndexPol0: %d") % startIndexPol0
    print ("startIndexPol1: %d") % startIndexPol1
  print ("countADCPol0[%d]: %d") % (startIndexPol0, countADCPol0[startIndexPol0])
  print ("countADCPol1[%d]: %d") % (startIndexPol1, countADCPol1[startIndexPol1])
  print ("startSyncADC: %d") % startSyncADC

  # Calculating where both files end overlaping.
  if (countADCPol0[-1] > countADCPol1[-1]):
    endSyncADC = countADCPol1[-1]
    endIndexPol0 = np.where(countADCPol0 == endSyncADC)[0][0]
    endIndexPol1 = countADCPol1.size - 1
    endIndex = endIndexPol0
    print ("endIndexPol0: %d") % endIndexPol0
    print ("endIndexPol1: %d") % endIndexPol1
    print ("endIndex: %d") % endIndex
  elif (countADCPol0[-1] < countADCPol1[-1]):
    endSyncADC = countADCPol0[-1]
    endIndexPol1 = np.where(countADCPol1 == endSyncADC)[0][0]
    endIndexPol0 = countADCPol0.size - 1
    endIndex = endIndexPol1
    print ("endIndexPol0: %d") % endIndexPol0
    print ("endIndexPol1: %d") % endIndexPol1
    print ("endIndex: %d") % endIndex
  else:
    endSyncADC = countADCPol0[-1]
    endIndexPol0 = endIndexPol1 = countADCPol0.size
  print ("countADCPol0[%d]: %d") % (endIndexPol0, countADCPol0[endIndexPol0])
  print ("countADCPol1[%d]: %d") % (endIndexPol1, countADCPol1[endIndexPol1])
  print ("endSyncADC: %d") % endSyncADC

  # Getting difference between countADC to check for missing packets.
  differencePol0 = np.diff(countADCPol0[startIndexPol0:])
  differencePol1 = np.diff(countADCPol1[startIndexPol1:])
  breaksPol0 = np.where(differencePol0 != 8192)[0]
  breaksPol1 = np.where(differencePol1 != 8192)[0]
  print "breaksPol0: ", breaksPol0
  print "breaksPol1: ", breaksPol1
  if (breaksPol0.size != 0):
    print ("Missing spectra in: %s") % (h5FilePol0)
    print "Missing spectra located at: ", breaksPol0
  if (breaksPol1.size != 0):
    print ("Missing spectra in: %s") % (h5FilePol1)
    print "Missing spectra located at: ", breaksPol1

  # Calculating sampling times, start MJD times, frequencies etc.
  outFileName = opts.outFileName
  print ("outFileName: %s") % outFileName
  chunkSize = opts.chunkSize
  print ("chunkSize: %d") % chunkSize
  samplingTime = complexChannels / samplingClock
  print ("Nyquist samplingTime: %.20f s") % samplingTime
  #samplingTime = 4.78504672897196
  decimationFactor = opts.decimationFactor
  if (decimationFactor > 1):
    samplingTime = samplingTime * decimationFactor
    print ("samplingTime: %.20f ms") % samplingTime
  else:
    print ("samplingTime: %.20f ms") % samplingTime

  # Check if decimationFactor is power of two, if not then quit.
  if( decimationFactor != 0 and ((decimationFactor & (decimationFactor - 1)) == 0) == False):
    print "Input error! decimationFactor not a power of two!"
    sys.exit(0)

  # Check if decimationFactor is greater than chunkSize.
  if (decimationFactor > chunkSize):
    chunkSize = 2 * decimationFactor
    print ("decimationFactor: %d") % decimationFactor
    print ("new chunkSize: %d") % chunkSize

  # Find sync time in the data files.
  try:
    syncTime = dataH5FilePol0["/TelescopeModel/cbf"].attrs['sync_time']
  except KeyError:
    print "Critical error! Data does not have sync time in the header! Specify it manually in the script!"
    sys.exit(0)
  #syncTime = 1462436476 # UTC sync time for first observation of Vela.
  print ("syncTime: %d") % syncTime
  obsStartTime = startSyncADC / samplingClock
  print ("obsStartTime: %.12f") % obsStartTime
  unixTime = float(syncTime) + obsStartTime
  print ("unixTime: %.12f") % unixTime
  decimalUnixTime = (str(unixTime - int(unixTime)))[1:]
  intUnixTime = int(unixTime)
  unixDateTime = datetime.datetime.utcfromtimestamp(intUnixTime).strftime("%Y-%m-%d %H:%M:%S")
  unixDateTime = unixDateTime + decimalUnixTime
  startTimeMJD = ephem.julian_date(ephem.Date(unixDateTime)) - 2400000.5 # convert to MJD
  print ("startTimeMJD: %.12f") % startTimeMJD
  freqCent = opts.freqCent
  print ("freqCent: %f") % freqCent
  freqTop = freqCent + (((channelNumberPol0 / 2) - 1) * channelBW)
  print ("freqTop: %f") % freqTop
  freqBottom = freqCent - (((channelNumberPol0 / 2)) * channelBW)
  print ("freqBottom: %f") % freqBottom
  sourceName = opts.sourceName
  print ("sourceName: %s") % sourceName
  rightAscension = opts.rightAscension
  print ("rightAscension: %s") % rightAscension
  declination = opts.declination
  print ("declination: %s") % declination

  # Creating and populating file header.
  fileOut = open(outFileName, "wab")
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
  header = "".join([header, _write_double("fch1", freqBottom)])
  header = "".join([header, _write_double("foff", channelBW)])
  #header = "".join([header, _write_double("fch1", freqTop)])
  #header = "".join([header, _write_double("foff", -1.0 * channelBW)])
  header = "".join([header, _write_int("nchans", channelNumberPol0)])
  header = "".join([header, _write_int("nbits", 32)])
  header = "".join([header, _write_double("tstart", startTimeMJD)])
  header = "".join([header, _write_double("tsamp", samplingTime)])
  if fullStokes:
    header = "".join([header, _write_int("nifs", 4)])
  else:
    header = "".join([header, _write_int("nifs", 1)])
  header = "".join([header, struct.pack("I", len(headerEnd)), headerEnd])
  fileOut.write(header)

  # Extracting data from h5 files and writing to filterbank file.
  #endIndex = 208985 # Number of Nyquist-sampled spectra in 1 second, use to process only 1 second of data.
  for t0 in range(0, endIndex, chunkSize):
    t1 = min(endIndex, t0 + chunkSize)
    spectraChunkPol0 = dataH5FilePol0["Data/bf_raw"][:, t0 + startIndexPol0:t1 + startIndexPol0, :]
    spectraChunkPol1 = dataH5FilePol1["Data/bf_raw"][:, t0 + startIndexPol1:t1 + startIndexPol1, :]
    spectraChunkComplexPol0 = spectraChunkPol0[...,0] + 1j * spectraChunkPol0[...,1]
    spectraChunkComplexPol1 = spectraChunkPol1[...,0] + 1j * spectraChunkPol1[...,1]
    if fullStokes:
      if (decimationFactor > 1):
        stokesI = ((((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) + (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).reshape(-1, (chunkSize / decimationFactor), decimationFactor).mean(axis = 2)).T
        stokesQ = ((((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) - (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).reshape(-1, (chunkSize / decimationFactor), decimationFactor).mean(axis = 2)).T
        stokesU = ((((spectraChunkComplexPol0 * spectraChunkComplexPol1.conjugate()) + (spectraChunkComplexPol0.conjugate() * spectraChunkComplexPol1)).real).reshape(-1, (chunkSize / decimationFactor), decimationFactor).mean(axis = 2)).T
        stokesV = ((((spectraChunkComplexPol0 * spectraChunkComplexPol1.conjugate()) - (spectraChunkComplexPol0.conjugate() * spectraChunkComplexPol1)).imag).reshape(-1, (chunkSize / decimationFactor), decimationFactor).mean(axis = 2)).T
        stokesIQUV = np.concatenate((stokesI, stokesQ, stokesU, stokesV), axis = 1)
        stokesIQUV = stokesIQUV.reshape((chunkSize * 4) / decimationFactor, channelNumberPol0)
      else:
        stokesI = (((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) + (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).T
        stokesQ = (((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) - (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).T
        stokesU = (((spectraChunkComplexPol0 * spectraChunkComplexPol1.conjugate()) + (spectraChunkComplexPol0.conjugate() * spectraChunkComplexPol1)).real).T
        stokesV = (((spectraChunkComplexPol0 * spectraChunkComplexPol1.conjugate()) - (spectraChunkComplexPol0.conjugate() * spectraChunkComplexPol1)).imag).T
        stokesIQUV = np.concatenate((stokesI, stokesQ, stokesU, stokesV), axis = 1)
        stokesIQUV = stokesIQUV.reshape(chunkSize * 4, channelNumberPol0)
      stokesIQUVFloat32 = stokesIQUV.astype(dtype = np.float32)
      bytesStokesIQUVFloat32 = stokesIQUVFloat32.tobytes(order = "C")
      fileOut.write(bytesStokesIQUVFloat32)
    else:
      if (decimationFactor > 1):
        stokesI = ((((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) + (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).reshape(-1, (chunkSize / decimationFactor), decimationFactor).mean(axis = 2)).T
      else:
        stokesI = (((spectraChunkComplexPol0 * spectraChunkComplexPol0.conjugate()) + (spectraChunkComplexPol1 * spectraChunkComplexPol1.conjugate())).real).T
      stokesIFloat32 = stokesI.astype(dtype = np.float32)
      bytesStokesIFloat32 = stokesIFloat32.tobytes(order = "C")
      fileOut.write(bytesStokesIFloat32)
  fileOut.close()
