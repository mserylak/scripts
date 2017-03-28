#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.


import os
import sys
import time
import argparse
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import cm
from sigpyproc.Readers import FilReader


__version__ = 1.2


# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = "plotFilterbank.py [options] --file <inputFile> ",
                                   description = "Plot band-passes, dynamic spectra or timeseries from SIGPROC filterbank files. Version %s" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2015 by Maciej Serylak")
  parser.add_argument("--file", dest = "filterbankFileName", action = "store", metavar = "<fileName>", default = "", help = "specify input file name")
  parser.add_argument("--spectrum", dest = "spectrum", action = "store", metavar = "<spectrumNumber>", type = int, help = "specify single spectrum to plot")
  parser.add_argument("--block", dest = "block", action = "store", metavar = "<startSpectrum> <endSpectrum>", default = "", help = "specify range of spectra to average and plot")
  parser.add_argument("--dynamic", dest = "dynamic", action = "store", metavar = "<startSpectrum> <endSpectrum>", default = "", help = "specify range of spectra and plot dynamic spectrum")
  parser.add_argument("--timeseries", dest = "timeseries", action = "store", metavar = "<channelNumber> <startSpectrum> <endSpectrum>", default = "", help = "specify single channel and range of spectra to plot timeseries")
  parser.add_argument("--bandpass", dest = "bandpass", action = "store_true", help = "plot total bandpass")
  parser.add_argument("--save", dest = "savePlot", action = "store_true", help = "save plot to .png file instead of interactive plotting")
  args = parser.parse_args()

  # Check for filterbankFileName presence.
  if not args.filterbankFileName:
    print parser.description, "\n"
    print "usage:", parser.usage, "\n"
    print parser.epilog
    sys.exit(0)
  else:
    filterbankFileName = args.filterbankFileName

  # Define constants and variables.
  filterbankFile = FilReader(filterbankFileName) # read filterbank file
  #print "File %s opened." % (filterbankFilename)
  numberChannels = filterbankFile.header.nchans # get number of spectral channels
  numberSpectra = filterbankFile.header.nsamples # get number of spectra/samples

  # Only one option for plotting is allowed.
  if (args.spectrum and args.dynamic) or\
    (args.spectrum and args.block) or\
    (args.spectrum and args.bandpass) or\
    (args.spectrum and args.timeseries) or\
    (args.dynamic and args.block) or\
    (args.dynamic and args.bandpass) or\
    (args.dynamic and args.timeseries) or\
    (args.block and args.bandpass) or\
    (args.block and args.timeseries):
    raise ValueError("Only one plotting option allowed.")

  print "File %s has %d channels and %d samples/spectra." % (filterbankFileName, numberChannels, numberSpectra)
  if args.spectrum:
    spectrum = args.spectrum
    if (spectrum >= numberSpectra):
      spectrum = numberSpectra-1
      print "Selected spectrum exceeds available number of spectra!"
    singleSpectrum = filterbankFile.readBlock(spectrum, 1) # read specific spectrum from the data
    plt.plot(singleSpectrum)
    plt.xlabel("Channel")
    plt.ylabel("Intensity (a.u.)")
    if not args.savePlot:
      plt.show()
    else:
      baseFilterbankFilename, extFilterbankFilename = os.path.splitext(filterbankFileName)
      plt.savefig(baseFilterbankFilename + "_spectrum_" + str(spectrum) + ".png")
      sys.exit(0)
  elif args.block:
    block = args.block.split()
    block = np.arange(int(block[0]), int(block[1]))
    #print block[0], block[-1]
    if (block[-1] >= numberSpectra):
      block[-1] = numberSpectra-1
      print "Selected spectrum exceeds available number of spectra!"
    blockSpectrum = filterbankFile.readBlock(block[0], block[-1]) # read specific spectrum from the data
    blockBandpass = blockSpectrum.get_bandpass() # calculate bandpass from entire observation
    plt.plot(blockBandpass)
    plt.xlabel("Channel")
    plt.ylabel("Intensity (a.u.)")
    if not args.savePlot:
      plt.show()
    else:
      baseFilterbankFilename, extFilterbankFilename = os.path.splitext(filterbankFileName)
      plt.savefig(baseFilterbankFilename + "_block_" + str(block[0]) + "-" + str(block[-1]) + ".png")
      sys.exit(0)
  elif args.dynamic:
    dynamic = args.dynamic.split()
    dynamic = np.arange(int(dynamic[0]), int(dynamic[1]))
    #print dynamic[0], dynamic[-1]
    if (dynamic[-1] >= numberSpectra):
      dynamic[-1] = numberSpectra-1
      print "Selected spectrum exceeds available number of spectra!"
    dynamicSpectrum = filterbankFile.readBlock(dynamic[0], dynamic[-1]) # read specific spectrum from the data
    plt.imshow(dynamicSpectrum, origin='lower', cmap = cm.hot, interpolation='nearest', aspect='auto')
    plt.colorbar()
    plt.xlabel("Spectrum")
    plt.ylabel("Channel")
    if not args.savePlot:
      plt.show()
    else:
      baseFilterbankFilename, extFilterbankFilename = os.path.splitext(filterbankFileName)
      plt.savefig(baseFilterbankFilename + "_dynamic_" + str(dynamic[0]) + "-" + str(dynamic[-1]) + ".png")
      sys.exit(0)
  elif args.timeseries:
    timeseries = args.timeseries.split()
    channel = int(timeseries[0])
    begin = int(timeseries[1])
    end = int(timeseries[2])
    #print begin,end,channel
    if (end >= numberSpectra):
      end = numberSpectra-1
      print "Selected spectrum exceeds available number of spectra!"
    if (channel >= numberChannels):
      channel = numberChannels-1
      print "Selected channel exceeds available number of channels!"
    timeseriesChannel = filterbankFile.getChan(channel)
    timeseriesChannel.shape
    timeseriesSelected = timeseriesChannel[begin:end]
    plt.plot(timeseriesSelected)
    plt.xlabel("Spectrum")
    plt.ylabel("Intensity (a.u.)")
    if not args.savePlot:
      plt.show()
    else:
      baseFilterbankFilename, extFilterbankFilename = os.path.splitext(filterbankFileName)
      plt.savefig(baseFilterbankFilename + "_timeseries_ch" + str(channel) + "_" + str(begin) + "-" + str(end) + ".png")
      sys.exit(0)
  elif args.bandpass:
    totalBandpass = filterbankFile.bandpass() # calculate bandpass from entire observation
    plt.plot(totalBandpass)
    plt.xlabel("Channel")
    plt.ylabel("Intensity (a.u.)")
    if not args.savePlot:
      plt.show()
    else:
      baseFilterbankFilename, extFilterbankFilename = os.path.splitext(filterbankFileName)
      plt.savefig(baseFilterbankFilename + "_bandpass.png")
      sys.exit(0)
  else:
    raise ValueError("No plotting options provided!")
