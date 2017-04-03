#!/usr/bin/env python

# Copyright (C) 2015 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import os
import optparse as opt
import sys
import numpy as np

# Main body of the script
if __name__=="__main__":
  # Parsing the command line options
  usage = "Usage: %prog --parset <parset_file>"
  cmdline = opt.OptionParser(usage)
  cmdline.formatter.max_help_position = 50 # increase space reserved for option flags (default 24), trick to make the help more readable
  cmdline.formatter.width = 200 # increase help width from 120 to 200
  cmdline.add_option('--parset', type = 'str', dest = 'pfile', default = '', metavar = '*.parset', help = 'Parset file with observation details.')
  cmdline.add_option('--subint', type = 'int', dest = 'subint', default = '5', help = 'Length of subintegration.')
  cmdline.add_option('--output', type = 'str', dest = 'output', help = 'Output file.')
  cmdline.add_option('--verbose', dest="verbose", action="store_true", help="Verbose mode.")

  # reading cmd options
  (opts, args) = cmdline.parse_args()

  if not opts.pfile:
    cmdline.print_usage()
    sys.exit(0)

  # Define constans and variables.
  subbandNumber = 512   # Number of subbands (fixed at 512)
  clockFrequency = 200.0   # Sample clock freq. MHz (typically 200)
  parsetFile = opts.pfile
  subintLength = opts.subint
  outputFile = opts.output
  verbose = opts.verbose
  tempFile = parsetFile.split('.')[0] + "_temp.jones"

  if not outputFile:
    outputFile = 'antennaJones_' + parsetFile.split('.')[0] + '.sh'

  with open(parsetFile, 'r') as searchFile:
    for line in searchFile:
      if 'Observation.startTime' in line:
        startTime = line.split('=')[1]
        startTime = startTime.strip(' []\'\n')
        #print startTime
      if 'Observation.Scheduler.taskDuration' in line:
        taskDuration = line.split('=')[1]
        taskDuration = taskDuration.strip(' []\'\n')
        #print taskDuration
      if 'Observation.VirtualInstrument.stationList' in line:
        stationList = line.split('=')[1]
        stationList = stationList.strip(' []\'\n')
        stationList = stationList.split(',')
        stationList.sort()
        stationList = [item.replace('HBA0', '') for item in stationList]
        stationList = [item.replace('HBA1', '') for item in stationList]
        newStationList = []
        for item in stationList:
          if item not in newStationList:
            newStationList.append(item)
      if 'Observation.Beam[0].angle1' in line:
        targetRightAscension = line.split('=')[1]
        targetRightAscension = targetRightAscension.strip(' []\'\n')
        #print targetRightAscension
      if 'Observation.Beam[0].angle2' in line:
        targetDeclination = line.split('=')[1]
        targetDeclination = targetDeclination.strip(' []\'\n')
        #print targetDeclination
      if 'Observation.Beam[0].subbandList' in line:
        subbandList = line.split('=')[1]
        subbandList = subbandList.strip(' []\'\n')
        subbandList = subbandList.split('..')
        #print subbandList
        subbandStart = (int(subbandList[0]))
        subbandEnd = (int(subbandList[1]))

  outputFile = open(outputFile, 'w')
  for subband in xrange(subbandStart, subbandEnd + 1, 1):
    subbandFrequency = (100 + (subband * clockFrequency / 2.0 / subbandNumber)) * 1000000
    if verbose:
      print "antennaJones.py Hamaker %s \"%s\" %s %d %s %s %10.1f >> %s" % (newStationList[0], startTime, taskDuration, subintLength, targetRightAscension, targetDeclination, subbandFrequency, tempFile)
    outputFile.write("antennaJones.py Hamaker %s \"%s\" %s %d %s %s %10.1f >> %s\n" % (newStationList[0], startTime, taskDuration, subintLength, targetRightAscension, targetDeclination, subbandFrequency, tempFile))
  outputFile.close()
