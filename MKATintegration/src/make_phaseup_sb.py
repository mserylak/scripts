"""Phase UP Schedule Block"""

from katuilib import obsbuild, ScheduleBlockTypes
from optparse import OptionParser
import katconf
import logging

APP_NAME = 'katscripts'

calibrators = {
               'PKS 0408-65':'PKS 0408-65 | J0408-6545, radec bfcal single_accumulation, 4:08:20.38, -65:45:09.1, (800.0 8400.0 -3.708 3.807 -0.7202)',
               'PKS 1934-63':'PKS 1934-63 | J1939-6342, radec bfcal single_accumulation, 19:39:25.03, -63:42:45.7, (200.0 12000.0 -11.11 7.777 -1.231)',
               '3C 286':'3C 286, radec bfcal single_accumulation, 13:31:08.29, +30:30:33.0, (1408.0 43200.0 0.956 0.584 -0.1644)',
               '1421-490':'1421-490, radec bfcal single_accumulation, 14:24:32.28, -49:13:49.30, (145. 99000. 6.0550 -4.1963 1.1975)',

              }

def main(options, args):
    # Setup configuration source
    katconf.set_config(katconf.environ(options.config))

    # Set up Python logging
    katconf.configure_logging(options.logging)
    logfile = "kat.%s" % APP_NAME
    logger = logging.getLogger(logfile)

    # Load the configuration
    sysconf = katconf.SystemConfig()

    db_uri = sysconf.conf.get("katobs","db_uri")

    logger.info("Logging started")
    logger.info("Katobs obsbuild: db_uri=%s Make a MANUAL Block" % db_uri)

    obs = obsbuild(user=options.user, db_uri=db_uri)
    print "===obs.status()==="
    obs.status()
    print "===obs.status()==="
    #Create a new sb
    sb_id_code = obs.sb.new(owner=options.user)
    print "===NEW SB CREATED===", sb_id_code
    description = "MKAIV 215: Phase-up (4K) "
    if options.calibrator is not None:
        description += options.calibrator
    obs.sb.description = description
    obs.sb.type = ScheduleBlockTypes.OBSERVATION
    obs.sb.instruction_set="run-obs-script /home/kat/katsdpscripts/AR1/observations/bf_phaseup_AR1.py '%s' -t 90 -n 'off' --description='%s'" % (options.target, description)
    obs.sb.antenna_spec = options.antennas
    obs.sb.controlled_resources_spec = 'cbf,sdp'
    obs.sb.to_defined()
    obs.sb.to_approved()
    obs.sb.unload()

    #Display the created sb
    print "\n===obs.sb==="
    print obs.sb

    logger.info("Katobs making Phase Up done.")

if __name__ == "__main__":
    parser = OptionParser()
    parser.add_option('-c', '--config',
                      dest='config',
                      type=str,
                      default="xmlrpc:http://monctl.mkat.karoo.kat.ac.za:2010",
                      metavar='CONF',
                      help='look for configuration files in folder CONF (default=%default)' )
    parser.add_option('-l', '--logging',
                      dest='logging',
                      type=str,
                      default=None,
                      metavar='LOGGING',
                      help='level to use for basic logging or name of logging configuration file; default is /log/log.<SITENAME>.conf')
    parser.add_option('-o', '--user',
                      dest='user',
                      type=str,
                      default=None,
                      help='The obsever/user/owner (non optional option)')
    parser.add_option('--target',
                      dest='target',
                      type=str,
                      default=None,
                      help='phase-up calibrator target, or calibrator selected from known list')
    parser.add_option('--ants',
                      dest='antennas',
                      type=str,
                      default='available',
                      help='antennas to use in the observation (default=%default)')
    parser.add_option('--cals',
                      dest='cals',
                      action="store_true",
                      default=False,
                      help="list calibrators available for phasing up")
    (options, args) = parser.parse_args()

    if options.cals:
        for cal in calibrators:
            print('%s : %s' % (cal, calibrators[cal]))
        import sys
        sys.exit(0)

    if options.user is None:
        print "A  obsever/user/owner name is needed for this script"
        raise SystemExit(parser.print_usage())

    options.calibrator = None
    if options.target is None:
        options.calibrator = calibrators.keys()[0]
    if options.target in calibrators.keys():
        options.calibrator = options.target
    if options.calibrator is not None:
        options.target = calibrators[options.calibrator]

    main(options, args)

# -fin-
