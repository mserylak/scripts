#!/usr/bin/env python

# Copyright (C) 2017 by Paul Scholz, Patrick Lazarus, Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import os
import sys
import time
import struct
import argparse
import warnings
import numpy as np
np.set_printoptions(threshold=np.nan)
from astropy.time import Time
import astropy.io.fits as pyfits
import matplotlib.pyplot as plt


__version__ = 1.2


telescopeIDs = {
"FAKE": 0,
"Fake": 0,
"fake": 0,
"Arecibo": 1,
"Arecibo 305m": 1,
"ARECIBO": 1,
"ARECIBO 305m": 1,
"Ooty": 2,
"OOTY": 2,
"ooty": 2,
"Nancay": 3,
"nancay": 3,
"NANCAY": 3,
"Parkes": 4,
"PARKES": 4,
"parkes": 4,
"Jodrell": 5,
"JODRELL": 5,
"jodrell": 5,
"GBT": 6,
"GMRT": 7,
"Effelsberg": 8,
"ATA": 9,
"UTR-2": 10,
"LOFAR": 11,
"MeerKAT": 64,
"MEERKAT": 64,
"meerkat": 64,
"Meerkat": 64}


machineIDs = {
"FAKE": 0,
"Fake": 0,
"fake": 0,
"PSPM": 1,
"Wapp": 2,
"WAPP": 2,
"AOFTM": 3,
"BCPM1": 4,
"BPP": 4,
"OOTY": 5,
"SCAMP": 6,
"GBT Pulsar Spigot":7,
"SPIGOT": 7,
"BG/P": 11,
"PDEV": 12,
"KAT": 64,
"Kat": 64,
"kat": 64}


headerParameters = {
"HEADER_START": "flag",
"telescope_id": "i",
"machine_id": "i",
"data_type": "i",
"rawdatafile": "str",
"source_name": "str",
"src_raj": "d",
"src_dej": "d",
"tstart": "d",
"tsamp": "d",
"nbits": "i",
"fch1": "d",
"foff": "d",
"nchans": "i",
"nifs": "i",
"HEADER_END": "flag"}


def prepareString(string):
  return struct.pack("i", len(string)) + string


def prepareDouble(key, value):
  return prepareString(key) + struct.pack("d", float(value))


def prepareInt(key, value):
  return prepareString(key) + struct.pack("i", int(value))


def addToHeader(parameterName, parameterValue):
  if headerParameters[parameterName] == "d":
    return prepareDouble(parameterName, parameterValue)
  elif headerParameters[parameterName] == "i":
    return prepareInt(parameterName, parameterValue)
  elif headerParameters[parameterName] == "str":
    return prepareString(parameterName) + prepareString(parameterValue)
  elif headerParameters[parameterName] == "flag":
    return prepareString(parameterName)
  else:
    print "Unknown key: %s" % parameterName
  return packedStructHeader


def unpack2Bit(data):
  """
  Unpack 2-bit data that has been read in as bytes.
    Input:
      data2bit: array of unsigned 2-bit ints packed into
                an array of bytes (8 bit).
    Output:
      outdata: unpacked array. The size of this array will
               be four times the size of the input data.
  """
  piece0 = np.bitwise_and(data >> 0x06, 0x03)
  piece1 = np.bitwise_and(data >> 0x04, 0x03)
  piece2 = np.bitwise_and(data >> 0x02, 0x03)
  piece3 = np.bitwise_and(data, 0x03)
  return np.dstack([piece0, piece1, piece2, piece3]).flatten()


def unpack4Bit(data):
  """
  Unpack 4-bit data that has been read in as bytes.
    Input:
      data4bit: array of unsigned 4-bit ints packed into
                an array of bytes.
    Output:
      outdata: unpacked array. The size of this array will
               be twice the size of the input data.
  """
  piece0 = np.bitwise_and(data >> 0x04, 0x0F)
  piece1 = np.bitwise_and(data, 0x0F)
  return np.dstack([piece0, piece1]).flatten()


def getWeights(data, iSub):
  """
  Return weights for a particular subint.
    Inputs:
      data: PyFITS object.
      iSub: index of subint (first subint is 0).
    Output:
       weights: subint weights (there is one value for each channel).
  """
  return data["SUBINT"].data[iSub]["DAT_WTS"]


def getScales(data, iSub):
  """
  Return scales for a particular subint.
    Inputs:
      data: PyFITS object.
      iSub: index of subint (first subint is 0).
    Output:
      scales: subint scales (there is one value for each channel).
  """
  return data["SUBINT"].data[iSub]["DAT_SCL"]


def getOffsets(data, iSub):
  """
  Return offsets for a particular subint.
    Inputs:
      data: PyFITS object.
      iSub: index of subint (first subint is 0).
    Output:
      offsets: subint offsets (there is one value for each channel).
  """
  return data["SUBINT"].data[iSub]["DAT_OFFS"]


def translateHeader(fitsObject):
  """
  Return SIGPROC filterbank header.
    Inputs:
      data: PyFITS object.
    Output:
      header: dictionary with filterbank header keys and values.
  """
  psrfitsHeader = fitsObject[0].header
  subintHeader = fitsObject["SUBINT"].header
  filterbankHeader = {}
  if psrfitsHeader["TELESCOP"] in telescopeIDs:
    filterbankHeader["telescope_id"] = telescopeIDs[psrfitsHeader["TELESCOP"]]
  else:
    filterbankHeader["telescope_id"] = -1
  if psrfitsHeader["BACKEND"] in machineIDs:
    filterbankHeader["machine_id"] = machineIDs[psrfitsHeader["BACKEND"]]
  else:
    filterbankHeader["machine_id"] = -1
  filterbankHeader["data_type"] = 1
  filterbankHeader["rawdatafile"] = fitsObject.filename()
  filterbankHeader["source_name"] = psrfitsHeader["SRC_NAME"]
  filterbankHeader["src_raj"] = float(psrfitsHeader["RA"].replace(":",""))
  filterbankHeader["src_dej"] = float(psrfitsHeader["DEC"].replace(":",""))
  filterbankHeader["tstart"] = psrfitsHeader["STT_IMJD"] + ((psrfitsHeader["STT_SMJD"] + psrfitsHeader["STT_OFFS"]) / 86400.0)
  filterbankHeader["tsamp"] = subintHeader["TBIN"]
  filterbankHeader["nbits"] = None
  filterbankHeader["fch1"] = psrfitsHeader["OBSFREQ"] + np.abs(psrfitsHeader["OBSBW"]) / 2.0 - np.abs(subintHeader["CHAN_BW"]) / 2.0
  filterbankHeader["foff"] = -1.0 * np.abs(subintHeader["CHAN_BW"])
  filterbankHeader["nchans"] = subintHeader["NCHAN"]
  filterbankHeader["nifs"] = None
  return filterbankHeader


def readSubint(fitsObject, iSub, applyWeights = True, applyScales = True, applyOffsets = True, sumIFs = False):
  """
  Read a PSRFITS subint from a open pyfits file object.
  Applies scales, weights, and offsets to the data.
    Inputs:
      iSub: index of subint (first subint is 0)
      applyWeights: if True, apply weights.
                     (Default: apply weights)
      applyScales: if True, apply scales.
                     (Default: apply scales)
      applyOffsets: if True, apply offsets.
                     (Default: apply offsets)
      sumIFs: sum AA and BB to form total-power data.
                     (Default: do not sum)
    Output:
      data: Subint data with scales, weights, and offsets
            applied in float32 dtype with shape (nsamps,npol,nchan).
  """
  subintData = fitsObject["SUBINT"].data[iSub]["DATA"]
  nBits = fitsObject["SUBINT"].header["NBITS"]
  nSampPerSubint = fitsObject["SUBINT"].header["NSBLK"]
  nChan = fitsObject["SUBINT"].header["NCHAN"]
  nPol = fitsObject["SUBINT"].header["NPOL"]
  #subintDataShape = subintData.shape
  #if ((nBits < 8) and (subintDataShape[0] != nSampPerSubint) and (subintDataShape[2] != nChan * (nBits / 8.0))):
  #  #subintData = subintData.reshape(nSampPerSubint, nPol, nChan * (nBits / 8.0))
  #  subintData = subintData.reshape(int((nSampPerSubint) * (nBits / 8.0)), nPol, nChan)
  #if nBits == 4:
  #  data = unpack4Bit(subintData)
  #elif nBits == 2:
  #  data = unpack2Bit(subintData)
  #else:
  #  data = np.array(subintData)
  data = np.array(subintData)
  if applyOffsets:
    offsets = getOffsets(fitsObject, iSub)
    offsets = offsets.reshape((nPol, nChan))
  else:
    offsets = 0
  if applyScales:
    scales = getScales(fitsObject, iSub)
    scales = scales.reshape((nPol, nChan))
  else:
    scales = 1
  if applyWeights:
    weights = getWeights(fitsObject, iSub)
  else:
    weights = 1
  #data = data.reshape(nSampPerSubint, nPol, nChan)
  dataWSO = ((data * scales) + offsets) * weights
  if nPol == 2 or nPol == 4:
    if sumIFs == True:
      dataWSO = dataWSO[:, 0, :] + dataWSO[:, 1, :]
  return dataWSO


# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "PSRFITS2fil.py [options] --file <inputFits> ",
                                   description = "Convert PSRFITS data into SIGPROC filterbank data file. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Paul Scholz, Patrick Lazarus, Maciej Serylak")
  parser.add_argument("--file", dest = "psrfitsFileName", action = "store", metavar = "<fileName>", default = "", help = "specify input file name")
  parser.add_argument("--nBit", dest = "nBitsOut", action = "store", metavar = "<nBits>", default = 32, type = int, help = "specify number of bits in the output .fil file (default: 32)")
  parser.add_argument("--out", dest = "outFileName", action = "store", metavar = "<outFileName>", default = "", help = "specify output filterbank file name (default: replace input extension with .fil)")
  parser.add_argument("--nSub", dest = "nSubProcess", action = "store", metavar = "<nSubs>", default = "", help = "specify number of sub-integrations to process (default: process all)")
  parser.add_argument("--sumIFs", dest = "sumIFs", action = "store_true", help = "form total-power data")
  parser.add_argument("--noweights", dest = "applyWeights", action = "store_false", help = "do not apply weights when converting data")
  parser.add_argument("--noscales",  dest = "applyScales",  action = "store_false", help = "do not apply scales when converting data")
  parser.add_argument("--nooffsets", dest = "applyOffsets", action = "store_false", help = "do not apply offsets when converting data")
  args = parser.parse_args()

  # Start script timing.
  scriptStartTime = time.time()

  # Check for psrfitsFileName presence.
  if not args.psrfitsFileName:
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)
  else:
    psrfitsFileName = args.psrfitsFileName

  # Check for nBits presence.
  nBitsOut = args.nBitsOut
  if nBitsOut >= 4 and (nBitsOut == 32 or nBitsOut == 16 or nBitsOut == 8):
    pass
  else:
    raise ValueError("Converting to %d-bit data not supported." % nBitsOut)

  # Check for outFileName presence.
  if args.outFileName:
    outFileName = args.outFileName
  else:
    outFileName = '.'.join(psrfitsFileName.split('.')[:-1]) + ".fil"

  # Opening PSRFITS file.
  psrfitsFile = pyfits.open(psrfitsFileName, mode = "readonly", memmap = True)
  nBits = psrfitsFile["SUBINT"].header["NBITS"]
  if nBits != 8:
    raise ValueError("Reading %d-bit data not supported." % nBits)

  # Checking number of available sub-integrations.
  nSubint = psrfitsFile["SUBINT"].header["NAXIS2"]
  if args.nSubProcess:
    nSubProcess = int(args.nSubProcess)
  else:
    nSubProcess = nSubint
  if nSubProcess >= nSubint:
    warnings.warn("Only %d sub-integrations available. Re-setting to available number of sub-integrations." % nSubint)
    nSubProcess = nSubint
  if nSubProcess < 0:
    raise ValueError("Cannot process negative number of sub-integrations.")

  # Creating and populating dictionary with SIGPROC header keys and values.
  sigprocHeader = translateHeader(psrfitsFile)
  sigprocHeader["nbits"] = nBitsOut

  # Check for sumIFs presence.
  sumIFs = args.sumIFs
  nPol = psrfitsFile["SUBINT"].header["NPOL"]
  polType = psrfitsFile["SUBINT"].header["POL_TYPE"]
  if nPol == 4 and (polType == "AABBCRCI" or polType == "XXYYCRCI" or polType == "LLRRCRCI"):
    if sumIFs:
      sigprocHeader["nifs"] = 1
    else:
      sumIFs = False
      sigprocHeader["nifs"] = nPol
  elif nPol == 2 and (polType == "AABB" or polType == "XXYY" or polType == "LLRR"):
    if sumIFs:
      sigprocHeader["nifs"] = 1
    else:
      sumIFs = False
      sigprocHeader["nifs"] = nPol
  elif nPol == 1 and (polType == "AA+BB" or polType == "INTEN"):
    if sumIFs:
      print "Data already in total power."
      sigprocHeader["nifs"] = 1
    else:
      sumIFs = False
      sigprocHeader["nifs"] = nPol
  else:
    raise ValueError("Unknown polarisation type: %s" % polType)

  # Create SIGPROC header. Only add recognized parameters.
  fileOut = open(outFileName, "wb")
  fileOut.write(addToHeader("HEADER_START", None))
  for parameterName in sigprocHeader.keys():
    if parameterName not in headerParameters:
      continue
    parameterValue = sigprocHeader[parameterName]
    #print "Writing SIGPROC header parameter: %s[\"%s\"]" % (parameterName, parameterValue)
    fileOut.write(addToHeader(parameterName, parameterValue))
  fileOut.write(addToHeader("HEADER_END", None))

  # Flip the band if frequency channels are in ascending order.
  if psrfitsFile["SUBINT"].header["CHAN_BW"] > 0:
    flipBand = True
    print "Fits file frequencies in ascending order. Flipping the frequency band."
  else:
    flipBand = False

  # Calculate scaling factor if output data is not 32 bits.
  if nBitsOut != 32:
    print "Calculating statistics on first sub-integration."
    subint0 = readSubint(psrfitsFile, 0, args.applyWeights, args.applyScales, args.applyOffsets, sumIFs)
    #newMax = np.mean(subint0) + 3 * np.std(subint0)
    newMax = 3 * np.median(subint0)
    #print "3 * median = %f" % newMax
    if newMax > 2.0**nBitsOut:
      scaleFlag = True
      scaleFactor = newMax / (2.0**nBitsOut)
      print "Scaling data by %f" % (1.0 / scaleFactor)
      print "Values larger than %f (pre-scaling) will be set to %f." % (newMax, (2.0**nBitsOut) - 1)
    else:
      scaleFlag = False
      scaleFactor = 1.0
      print "No scaling necessary."
  else:
      scaleFactor = 1.0
      print "No scaling necessary for 32-bit float output file."

  print "Writing data..."

  # Converting the data to SIGPROC filterbank.
  for iSub in range(nSubProcess):
    subint = readSubint(psrfitsFile, iSub, args.applyWeights, args.applyScales, args.applyOffsets, sumIFs)
    if flipBand:
      subint = np.fliplr(subint)
    subint /= scaleFactor
    if nBitsOut == 32:
      subint = subint.astype(dtype = np.float32)
    elif nBitsOut == 16:
      subint = subint.astype(dtype = np.uint16)
    elif nBitsOut == 8:
      subint = subint.astype(dtype = np.uint8)
    subint = subint.tobytes(order = "C")
    fileOut.write(subint)
  print "Done."
  fileOut.close()

  # End timing script and produce result.
  scriptEndTime = time.time()
  print "Script running time: %.1f s." % (scriptEndTime - scriptStartTime)
