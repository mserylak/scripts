#!/usr/bin/env python

# Make a table of subband number and equivalent.

# low / centre / high frequency for the RCU mode 5.

num_subbands = 512   # Number of subbands (fixed at 512)
clock_freq = 200.0   # Sample clock freq. MHz (typically 200)

print "Units = MHz"
print "Clock frequency =",clock_freq
print "Subband  LowFreq    MidFreq   HighFreq"
for subband in xrange(0,num_subbands,1):
  freq_low = ((subband-0.5) * clock_freq / 2.0 / num_subbands)
  freq_mid = (subband * clock_freq / 2.0 / num_subbands)
  freq_high = ((subband+0.5) * clock_freq / 2.0 / num_subbands)
  print "  %3d   %8.10f   %8.10f   %8.10f" % \
        (subband, freq_low, freq_mid, freq_high)
print "Done"
# End of file
