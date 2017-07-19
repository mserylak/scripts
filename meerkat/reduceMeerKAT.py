#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import os
import sys
import glob
import argparse
import subprocess
import time
import numpy as np
from matplotlib import cm
from matplotlib import colors
import psrchive
from coast_guard import cleaners
from coast_guard import clean_utils
from coast_guard import utils

__version__ = 1.0

def getArchiveInfo(archive):
  '''Query archive attributes.
    Input:
      archive: loaded PSRCHIVE archive object.
    Output:
      Print attributes of the archive.
'''
  fileName = archive.get_filename()
  nBin = archive.get_nbin()
  nChan = archive.get_nchan()
  nPol = archive.get_npol()
  nSubint = archive.get_nsubint()
  obsType = archive.get_type()
  telescopeName = archive.get_telescope()
  sourceName = archive.get_source()
  RA = archive.get_coordinates().ra()
  Dec = archive.get_coordinates().dec()
  centreFrequency = archive.get_centre_frequency()
  bandwidth = archive.get_bandwidth()
  DM = archive.get_dispersion_measure()
  RM = archive.get_rotation_measure()
  isDedispersed = archive.get_dedispersed()
  isFaradayRotated = archive.get_faraday_corrected()
  isPolCalib = archive.get_poln_calibrated()
  dataUnits = archive.get_scale()
  dataState = archive.get_state()
  obsDuration = archive.integration_length()
  obsStart = archive.start_time().fracday() + archive.start_time().intday()
  obsEnd = archive.end_time().fracday() + archive.end_time().intday()
  receiverName = archive.get_receiver_name()
  receptorBasis = archive.get_basis()
  backendName = archive.get_backend_name()
  backendDelay = archive.get_backend_delay()
  lowFreq = archive.get_centre_frequency() - archive.get_bandwidth() / 2.0
  highFreq = archive.get_centre_frequency() + archive.get_bandwidth() / 2.0
  print '\nfile             Name of the file                           %s' % fileName
  print 'nbin             Number of pulse phase bins                 %s' % nBin
  print 'nchan            Number of frequency channels               %s' % nChan
  print 'npol             Number of polarizations                    %s' % nPol
  print 'nsubint          Number of sub-integrations                 %s' % nSubint
  print 'type             Observation type                           %s' % obsType
  print 'site             Telescope name                             %s' % telescopeName
  print 'name             Source name                                %s' % sourceName
  print 'coord            Source coordinates                         %s%s' % (RA.getHMS(), Dec.getDMS())
  print 'freq             Centre frequency (MHz)                     %s' % centreFrequency
  print 'bw               Bandwidth (MHz)                            %s' % bandwidth
  print 'dm               Dispersion measure (pc/cm^3)               %s' % DM
  print 'rm               Rotation measure (rad/m^2)                 %s' % RM
  print 'dmc              Dispersion corrected                       %s' % isDedispersed
  print 'rmc              Faraday Rotation corrected                 %s' % isFaradayRotated
  print 'polc             Polarization calibrated                    %s' % isPolCalib
  print 'scale            Data units                                 %s' % dataUnits
  print 'state            Data state                                 %s' % dataState
  print 'length           Observation duration (s)                   %s' % obsDuration
  print 'start            Observation start (MJD)                    %.10f' % obsStart
  print 'end              Observation end (MJD)                      %.10f' % obsEnd
  print 'rcvr:name        Receiver name                              %s' % receiverName
  print 'rcvr:basis       Basis of receptors                         %s' % receptorBasis
  print 'be:name          Name of the backend instrument             %s' % backendName
  print 'be:delay         Backend propn delay from digi. input.      %s\n' % backendDelay

def getZeroWeights(archive, psrsh, verbose = False):
  '''Query the number of subint-channels with zeroed weights
    (i.e. cleaned) in TimerArchive/PSRFITS file.
       Input:
         archive: loaded PSRCHIVE archive object.
         psrsh: name of psrsh file
         verbose: verbosity flag
       Output:
         Writes out psrsh file with zap commands.
'''
  weights = archive.get_weights()
  (nSubint, nChan) = weights.shape
  if verbose:
    print '%s has %s subints and %s channels.' % (archive.get_filename(), nSubint, nChan)
  psrshFile = open(psrsh, 'w')
  psrshFile.write('#!/usr/bin/env psrsh\n\n')
  psrshFile.write('# Run with psrsh -e <ext> <script>.psh <archive>.ar\n\n')
  i = j = counter = spectrum = 0
  emptyChannels = [i for i in range(nChan)]
  for i in range(nSubint):
    spectrum = 0
    del emptyChannels[:]
    for j in range(nChan):
      if weights[i][j] == 0.0:
        counter += 1
        spectrum += 1
        emptyChannels.append(j)
    if verbose:
      percentSubint = (float(spectrum) / float(nChan)) * 100
      print 'Subint %s has %s channels (%.2f%%) set to zero. %s' % (i, spectrum, percentSubint, emptyChannels)
    for k in range(len(emptyChannels)):
      #print 'zap such %d,%d' % (i, empty_channels[k])
      np.savetxt(psrshFile, np.c_[i, emptyChannels[k]], fmt='zap such %d,%d')
  totalPercent = (float(counter)/float(weights.size)) * 100
  if verbose:
    print '%s data points out of %s with weights set to zero.' % (counter, weights.size)
    print '%.2f%% data points set to zero.' % (totalPercent)

# Main body of the script.
if __name__ == '__main__':
  # Parsing the command line options.
  parser = argparse.ArgumentParser(usage = 'reduceSingleStation.py --indir <inputDir> [options]',
                                   description = 'Reduce MeerKAT TimerArchive/PSRFITS data. Version %s' % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = 'Copyright (C) 2017 by Maciej Serylak')
  parser.add_argument('--indir', dest = 'inputDir', metavar = '<inputDir>', default = '', help = 'specify input directory')
  parser.add_argument('--outdir', dest = 'outputDir', metavar = '<outputDir>', default = '', help = 'specify output directory')
  parser.add_argument('--eph', dest = 'ephemFile', metavar = '<ephemFile>', default = '', help = 'use ephemeris file to update archives')
  parser.add_argument('--psrsh', dest = 'psrshSave', action='store_true', help='write zap commands to psrsh script file')
  args = parser.parse_args() # Reading command line options.

  # Start timing the script.
  scriptStartTime = time.time()

  # Check for inputDir presence.
  if not args.inputDir:
    print parser.description, '\n'
    print 'usage:', parser.usage, '\n'
    print parser.epilog
    sys.exit(0)

  # Validate writing permissions of inputDir.
  if os.access(args.inputDir, os.W_OK):
    pass
  else:
    print '\nInput directory without write permissions. Exiting script.\n'
    sys.exit(0)

  # Check for outputDir presence and validate writing permissions.
  if not args.outputDir:
    print '\nOption --outdir not specified. Selecting input directory.\n'
    outputDir = args.inputDir
  else:
    if os.access(args.outputDir, os.F_OK):
      pass
    else:
      print '\nOutput directory does not exist. Exiting script.\n'
      sys.exit(0)
    if os.access(args.outputDir, os.W_OK):
      pass
    else:
      print '\nOutput directory without write permissions. Exiting script.\n'
      sys.exit(0)

  # Read ephemeris and check if it conforms to standard (has EPHVER in it).
  # This is very rudimentary check. One should check for minimal set of values
  # present in the par file. More through checks are on TODO list.
  ephemFile = args.ephemFile
  if not ephemFile:
    print '\nOption --eph not specified. Continuing without updating ephemeris.\n'
    updateEphem = False
  else:
    if 'EPHVER' not in open(ephemFile).read():
      print '\nProvided file does not conform to ephemeris standard. Exiting script.\n'
      sys.exit(0)
    else:
      updateEphem = True
      print '\nProvided file %s does conform to ephemeris standard.\n' % ephemFile

  # Check for TimerArchive/PSRFITS files and add them together.
  inputFiles = []
  inputDir = args.inputDir + '/'
  for file in os.listdir(inputDir):
    if file.endswith('.ar'):
      inputFiles.append(file)
  inputFiles.sort()
  if len(inputFiles) < 1:
    print '\nFound no matching TimerArchive/PSRFITS files. Exiting script.\n'
    sys.exit(0)
  archives = []
  archives = [psrchive.Archive_load(inputDir + file) for file in inputFiles]
  #print archives[0]
  for i in range(1, len(archives)):
    #print archives[i]
    archives[0].append(archives[i])

  # Prepare new data object and set file name (PSR_DYYYYMMDDTHHMMSS.ar convention).
  rawArchive = archives[0].clone()
  stemFileName = rawArchive.get_source() + '_D' + os.path.split(rawArchive.get_filename())[-1].replace('-','').replace(':','')[:-3]

  # Update ephemeris.
  if updateEphem:
    print '\nUpdating ephemeris in: %s\n' % rawArchive.get_filename()
    rawArchive.set_ephemeris(ephemFile)

  # Clean archive from RFI and save zap commands to psrsh file.
  cleaner = cleaners.load_cleaner('surgical')
  surgicalParameters = 'chan_numpieces=1,subint_numpieces=1,chanthresh=3,subintthresh=3'
  cleaner.parse_config_string(surgicalParameters)
  print '\nCleaning archive from RFI.\n'
  cleaner.run(rawArchive)
  if args.psrshSave:
    psrshFilename = outputDir + '/' + stemFileName + '.psh'
    #print psrshFilename
    getZeroWeights(rawArchive, psrshFilename)
  print '\nSaving data to file %s\n' % (stemFileName + '.zap')
  rawArchive.unload(outputDir + '/' + stemFileName + '.zap')

  # End timing the script and output running time.
  scriptEndTime = time.time()
  print '\nScript running time: %.1f s.\n' % (scriptEndTime - scriptStartTime)
