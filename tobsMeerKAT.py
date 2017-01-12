#!/usr/bin/env python

# Copyright (C) 2017 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.

import argparse
import subprocess
import sys
import numpy as np

__version__ = 1.0

# Main body of the script.
if __name__=="__main__":
  # Parsing the command line options.
  parser = argparse.ArgumentParser(prog = "tobsMeerKAT.py",
                                   usage = "%(prog)s [options]",
                                   description = "Calculate sensitivity for MeerKAT. Version %.1f" % __version__,
                                   formatter_class = lambda prog: argparse.HelpFormatter(prog, max_help_position=100, width = 250),
                                   epilog = "Copyright (C) 2017 by Maciej Serylak")
  parser.add_argument("--npol",  type = int,   dest = "nPol",  metavar = "<nPol>",  default = "2" ,      help = "number of polarisations, (default: 2)")
  parser.add_argument("--bw",    type = float, dest = "BW",    metavar = "<BW>",    default = "770.0" ,  help = "observation bandwidth, (default: 770 MHz)")
  parser.add_argument("--f",     type = float, dest = "freq",  metavar = "<freq>",  default = "1284.0" , help = "frequency of observation, (default: 1284 MHz)")
  parser.add_argument("--sefd",  type = float, dest = "SEFD",  metavar = "<SEFD>",  default = "456" ,    help = "system equivalent flux density for individual antenna, (default: 456 Jy)")
  parser.add_argument("--nant",  type = int,   dest = "nAant", metavar = "<nAnt>",  default = "16",      help = "number of antennas used in observation, (default: 16)")
  parser.add_argument("--snr",   type = float, dest = "SNR",   metavar = "<SNR>",   default = "100.0",   help = "desired signal-to-noise ratio, (default: 100)")
  parser.add_argument("--p0",    type = float, dest = "p0",    metavar = "<P0>",    default = "1.0",     help = "pulsar period, (default: 1.0 s)")
  parser.add_argument("--w50",   type = float, dest = "w50",   metavar = "<w50>",   default = "0.05",    help = "width of pulse, (default: 0.05 * P0)")
  parser.add_argument("--s1400", type = float, dest = "S1400", metavar = "<S1400>", default = "10",      help = "minimal detectable flux at 1400 MHz, (default: 10 mJy)")
  parser.add_argument("--alpha", type = float, dest = "alpha", metavar = "<alpha>", default = "-1.6",    help = "spectral index, (default: -1.6)")
  parser.add_argument("--psr",                 dest = "PSR",   metavar = "<PSR>",   default = None,      help = "provide pulsar name (overrides --p0, --smin, --w50 and --alpha from psrcat unless unknown)")
  args = parser.parse_args() # Reading command line options.

  if len(sys.argv) == 1:
    parser.print_help()
    sys.exit(1)

  # Assign variables.
  nPol = args.nPol
  BW = args.BW
  freq = args.freq
  SEFD = args.SEFD
  nAnt = args.nAant
  SEFDn = SEFD / nAnt
  p0 = args.p0
  w50 = args.w50 * p0
  SNR = args.SNR
  S1400 = args.S1400
  alpha = args.alpha
  psrName = args.PSR

  # Check if --psr option was given as it overrides --w50, --p0, --smin and --alpha.
  if not psrName == None:
    print "\nPulsar name provided. Overriding --w50, --p0, --smin and --alpha with values from psrcat.\n"
    cmd = ["psrcat", "-nohead", "-o", "short", "-c", "JNAME P0 W50 S1400 SPINDX", psrName]
    pulsar = subprocess.Popen(cmd, shell=False, cwd=".", stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    (stdoutdata, stderrdata) = pulsar.communicate()
    returnCode = pulsar.returncode
    if returnCode != 0:
      print "\nProblems with psrcat: %s Exiting script.\n" % stdoutdata
      sys.exit(1)
    elif " not in catalogue" in stdoutdata:
      print "\nPulsar not found in psrcat. Exiting script.\n"
      sys.exit(1)
    psrJName = stdoutdata.split()[1]
    psrPeriod = float(stdoutdata.split()[2])
    # Checking if psrW50, psrS1400 and psrAlpha have numerical representation as psrcat inserts "*".
    psrW50 = stdoutdata.split()[3]
    if psrW50 == "*":
      print "\nNo W50 available in psrcat. Will assume: W50 = 0.05 * P0\n"
      psrW50 = psrPeriod * 0.05
    else:
      psrW50 = float(psrW50) * 0.001
    # Search if --w50 option was specified, if yes use it instead of psrcat value.
    resultW50 = any("--w50" in option for option in sys.argv)
    if resultW50:
      psrW50 = w50
    psrAlpha = stdoutdata.split()[5]
    if psrAlpha == "*":
      print "\nNo SPINDX available in psrcat. Will assume: SPINDX = %.1f\n" % alpha
      psrAlpha = alpha
    else:
      psrAlpha = float(psrAlpha)
    # Search if --alpha option was specified, if yes use it instead of psrcat value.
    resultAlpha = any("--alpha" in option for option in sys.argv)
    if resultAlpha:
      psrAlpha = alpha
    psrS1400 = stdoutdata.split()[4]
    if psrS1400 == "*":
      print "\nNo S1400 available in psrcat. Will assume S1400 = %.f.\n" % S1400
      psrS1400 = S1400
    else:
      psrS1400 = float(psrS1400)
    # Search if --s1400 option was specified, if yes use it instead of psrcat value.
    resultS1400 = any("--s1400" in option for option in sys.argv)
    if resultS1400:
      psrS1400 = S1400
    # Now will calculate tmin according to Weltevrede et al. 2006, A&A, 445, 243W.
    tmin = ((SNR*SNR * SEFDn*SEFDn) / (nPol * BW * (psrS1400*psrS1400))) * (psrW50 / (psrPeriod - psrW50))
    if tmin < psrPeriod:
      print "\nUsing %d antennas will result in detection of single pulses from pulsar %s.\n" % (nAnt, psrJName)
    else:
      print "\nIn order to achieve SNR of %.2f, pulsar %s needs to be observed for %.2f seconds at the frequency of %.2f MHz and with bandwidth of %.2f MHz.\n" % (SNR, psrJName, tmin, freq, BW)
  else:
    # Now will calculate tmin according to Weltevrede et al. 2006, A&A, 445, 243W.
    tmin = ((SNR*SNR*SEFDn*SEFDn)/(nPol*BW*(S1400*S1400)))*(w50/(p0-w50))
    if tmin < p0:
      print "\nUsing %d antennas will result in detection of single pulses from the source of interest.\n" % (nAnt)
    else:
      print "\nIn order to achieve SNR of %.2f source needs to be observed for %.2f seconds at the frequency of %.2f MHz and with bandwidth of %.2f MHz.\n" % (SNR, tmin, freq, BW)
