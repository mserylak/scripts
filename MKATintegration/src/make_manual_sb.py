"""Manual Schedule Block"""

from katuilib import obsbuild, ScheduleBlockTypes
from optparse import OptionParser
import katconf
import logging

APP_NAME = 'katscripts'

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
    obs.sb.description = "MANUAL block"
    obs.sb.notes = "This is a MANUAL block"
    obs.sb.type = ScheduleBlockTypes.MANUAL
    obs.sb.antenna_spec = 'available'
    obs.sb.controlled_resources_spec = 'cbf,sdp'
    obs.sb.to_defined()
    obs.sb.to_approved()
    obs.sb.unload()

    #Display the created sb
    print "\n===obs.sb==="
    print obs.sb

    logger.info("Katobs making MANUAL Block done.")

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
    (options, args) = parser.parse_args()
    if options.user is None:
        print "A  obsever/user/owner name is needed for this script"
        raise SystemExit(parser.print_usage())

    main(options, args)

# -fin-
