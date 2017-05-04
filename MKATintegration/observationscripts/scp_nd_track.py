#!/usr/bin/python
# Track target(s) for a specified time.

import time

from katcorelib import standard_script_options, verify_and_connect, collect_targets, start_session, user_logger

# Set logger to info level
## https://docs.python.org/2/howto/logging.html
#CRITICAL 50
#ERROR    40
#WARNING  30
#INFO     20
#DEBUG    10
#NOTSET   0
user_logger.setLevel(20)

# Set up standard script options
parser = standard_script_options(usage="%prog [options] <target>",
                                 description='Track a target for a specified time, while cycling noise diode on/off times as a percentage of dump rate.')
# Add experiment-specific options
parser.add_option('--track',
                  type=float,
                  default=600.,
                  help='Track time in seconds')

# Set default value for any option (both standard and experiment-specific options)
# KAT-7: parser.set_defaults(description='SCP ND track',dump_rate=0.25)
parser.set_defaults(description='SCP ND track')
# Parse the command line
opts, args = parser.parse_args()

if len(args) == 0:
    raise ValueError("Please specify a target argument")

# Setup noise diode cycle-on percentages
import numpy
cycle_on_frac = numpy.hstack((numpy.arange(50, 10, -5), numpy.arange(10, 1, -1), numpy.arange(1, 0., -0.1)))

# Check options and build KAT configuration, connecting to proxies and devices
with verify_and_connect(opts) as kat:
    observation_sources = collect_targets(kat, args)

    # Quit early if there are no sources to observe
    if len(observation_sources.filter(el_limit_deg=opts.horizon)) == 0:
        user_logger.warning("No targets are currently visible - please re-run the script later")
    else:
        # Start capture session, which creates HDF5 file
        with start_session(kat, **vars(opts)) as session:
            session.standard_setup(**vars(opts))
            # Iterate through source list, picking the next one that is up
            user_logger.info("Initiate capture start %d" % time.time())
            session.capture_start()

            # Noise diode cycle time set relative to track time
            for target in observation_sources.iterfilter(el_limit_deg=opts.horizon):
                user_logger.info("Initiating %g-second track on target '%s'" % (opts.track, target.name,))
                # Track without noise diode
                session.fire_noise_diode('coupler', on=0, off=0, period=-1)
                session.label('track')
                session.track(target, duration=opts.track)

                # Set noise diode fire to different periods
                for cycle_on in cycle_on_frac:
                    user_logger.info("Noise diode will be switched on %.2f%% of the time for %.2f sec cycle length" % (cycle_on, opts.track))
                    ontime = opts.track*(cycle_on/100.)
                    offtime = opts.track - ontime
                    user_logger.info("Setting up noise source pattern: %.3f s on and %.3f s off" % (ontime, offtime))
                    session.label('track')
                    session.fire_noise_diode('coupler', on=ontime, off=offtime, align=False)
                    user_logger.info('Tracking for %.3f seconds' % offtime)
                    session.track(target, duration=offtime)

                # Track without noise diode
                session.fire_noise_diode('coupler', on=0, off=0, period=-1)
                session.label('track')
                session.track(target, duration=opts.track)
# -fin-
