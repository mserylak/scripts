# Simple characterisation of noise diode
from datetime import datetime
from optparse import OptionParser
import ephem
import h5py
import matplotlib
import matplotlib.pyplot as plt
import numpy


def characterise_nd(
                    h5file,
                    metadata,
                    clockcounts,
                    n_sec=1.0,
                    verbose=False,
                   ):
    h5 = h5py.File(h5file, 'r')
    rawdata = h5[metadata['rawdata']]
    # display n seconds worth of data
    clks_nsec = metadata['clks_per_sec'] * n_sec

    adc_clks = numpy.array(clockcounts, dtype=float)
    unix_ts = float(metadata['clk_sync']) + adc_clks/float(metadata['fs'])
    raw_data_nsec = rawdata[:, :int(clks_nsec), :]
    ts = [datetime.utcfromtimestamp(ts) for ts in unix_ts[:int(clks_nsec)]]
    amplitude = numpy.sqrt(
                            numpy.array(raw_data_nsec[:, :, 0], dtype=float) ** 2
                            +
                            numpy.array(raw_data_nsec[:, :, 1], dtype=float) ** 2
                          )

    # simple characterisation tests
    tseries = numpy.median(amplitude, axis=0)
    fwrd_diff = numpy.diff(tseries)
    threshold = 10.*numpy.std(fwrd_diff)
    nd_boundary = numpy.nonzero(numpy.abs(fwrd_diff) > threshold)[0]
    nd_boundary = nd_boundary[numpy.nonzero(numpy.diff(nd_boundary) > 1)[0]+1]
    dt = numpy.mean([dt.total_seconds() for dt in numpy.diff(ts)])
    std_arr = [numpy.std(tseries[trans:nd_boundary[idx+1]]) for idx, trans in enumerate(nd_boundary[:-1])]

    nd_on_idx = []
    nd_off_idx = []
    for cnt, nd_boundary_idx in enumerate(nd_boundary):
        trans_range = numpy.arange(nd_boundary_idx-10, nd_boundary_idx+10)
        nd_boundary_region = tseries[trans_range]

        if verbose:
            plt.figure(figsize=(15, 9))
            plt.clf()
            on = nd_boundary_region > numpy.mean(tseries)
            plt.plot(trans_range[on], nd_boundary_region[on], 'r.', label='ND on')
            off = nd_boundary_region < numpy.mean(tseries)
            plt.plot(trans_range[off], nd_boundary_region[off], 'b.', label='ND off')
            plt.axvline(x=trans_range[len(trans_range)/2:len(trans_range)/2+2].mean(), color='k', linestyle='--', label='nd_boundary')
            trans_dt = (ts[len(trans_range)/2+2]-ts[len(trans_range)/2-1]).total_seconds()
            plt.axvline(x=trans_range[len(trans_range)/2]-0.5, color='c', linestyle=':', label=r'Transition region %.1f$\mu$s' % (trans_dt*1e6))
            plt.axvline(x=trans_range[len(trans_range)/2+2]+0.5, color='c', linestyle=':')
            plt.legend(loc=0)
            plt.xlabel('ADC clock counts')
            plt.ylabel('Noise Diode Transition')

        nd_on = numpy.nonzero(nd_boundary_region > numpy.mean(tseries))[0]
        if nd_on[0] == 0:
            nd_off_idx.append(nd_boundary_idx-10+nd_on[-1]+1)
        else:
            nd_on_idx.append(nd_boundary_idx-10+nd_on[0])
    nidx = numpy.min((len(nd_on_idx), len(nd_off_idx)))
    nd_on_idx = numpy.array(nd_on_idx)[:nidx]
    nd_off_idx = numpy.array(nd_off_idx)[:nidx]
    nd_period_list = numpy.hstack((numpy.diff(nd_on_idx), numpy.diff(nd_off_idx)))
    nd_period = numpy.median(numpy.hstack((numpy.diff(nd_on_idx), numpy.diff(nd_off_idx))))
    if nd_on_idx[0] < nd_off_idx[0]:
        # first boundary is on
        duty_cycle_on = numpy.median(numpy.abs(nd_off_idx - nd_on_idx))
        duty_cycle_off = nd_period - duty_cycle_on
        on_std = numpy.mean(std_arr[::2])
        off_std = numpy.mean(std_arr[1::2])
    else:
        # first boundary is off
        duty_cycle_off = numpy.median(numpy.abs(nd_on_idx - nd_off_idx))
        duty_cycle_on = nd_period - duty_cycle_off
        off_std = numpy.mean(std_arr[::2])
        on_std = numpy.mean(std_arr[1::2])
    print('ND period %d samples: noise diode on for %d sample and noise diode off for %d samples' % (nd_period, numpy.round(duty_cycle_on), numpy.round(duty_cycle_off)))

    plt.figure(figsize=(15, 9))
    plt.clf()
    plt.subplot(2, 1, 1)
    plt.semilogy(ts, tseries, 'c,', label='Timeseries')
    plt.axvline(x=ts[nd_on_idx[0]], color='r', linestyle='--', label='ND on')
    plt.axvline(x=ts[nd_off_idx[0]], color='b', linestyle='--', label='ND off')
    plt.axhline(y=numpy.mean(tseries), color='k', linestyle='--')
    for boundary_idx in nd_boundary:
        plt.axvline(x=ts[boundary_idx], color='k', linestyle=':')
    for on_idx in nd_on_idx[1:]:
        plt.axvline(x=ts[on_idx], color='r', linestyle='--')
    for off_idx in nd_off_idx[1:]:
        plt.axvline(x=ts[off_idx], color='b', linestyle='--')
    plt.axis('tight')
    plt.legend(loc=0)
    plt.title('Noise diode duty cycle %.3f s (on/off = %.3f/%.3f s)' % (dt*nd_period, dt*duty_cycle_on, dt*duty_cycle_off))
    plt.ylabel('Noise Diode Pattern [log]')

    plt.subplot(2, 1, 2)
    nrm_arr = tseries[:nd_boundary[0]]-numpy.mean(tseries[:nd_boundary[0]])
    std_arr = numpy.ones((nd_boundary[0], 1))*numpy.std(tseries[:nd_boundary[0]]-numpy.mean(tseries[:nd_boundary[0]]))
    for idx, trans in enumerate(nd_boundary[:-1]):
        nrm_arr = numpy.hstack([nrm_arr, tseries[trans:nd_boundary[idx+1]]-numpy.mean(tseries[trans:nd_boundary[idx+1]])])
        std_arr = numpy.vstack([std_arr, numpy.ones((nd_boundary[idx+1]-trans, 1))*numpy.std(tseries[trans:nd_boundary[idx+1]]-numpy.mean(tseries[trans:nd_boundary[idx+1]]))])
    nrm_arr = numpy.hstack([nrm_arr, tseries[nd_boundary[-1]:]-numpy.mean(tseries[nd_boundary[-1]:])])
    std_arr = numpy.vstack([std_arr, numpy.ones((len(tseries)-nd_boundary[-1], 1))*numpy.std(tseries[nd_boundary[-1]:]-numpy.mean(tseries[nd_boundary[-1]:]))])

    plt.plot(ts[nd_boundary[0]:], nrm_arr[nd_boundary[0]:], 'c.')
    plt.plot(ts[nd_boundary[0]:], std_arr[nd_boundary[0]:], 'k-')
    for boundary_idx in nd_boundary:
        plt.axvline(x=ts[boundary_idx], color='k', linestyle=':')
    plt.xlim(ts[0], ts[-1])
    plt.xlabel('Samples [sec]')
    plt.ylabel('Std Dev')
    plt.title('SDev ND on %.3f, SDev ND off %.3f' % (on_std, off_std))
    plt.gca().xaxis.set_major_formatter(matplotlib.dates.DateFormatter("%S.%f"))
    plt.gcf().autofmt_xdate()

    if verbose:
        plt.figure(figsize=(15, 9))
        plt.clf()
        plt.subplot(2, 1, 1)
        plt.semilogy(numpy.median(amplitude, axis=0), 'b')
        plt.axis('tight')
        plt.ylabel('Noise Diode Pattern')
        plt.xlabel('Clocks [counts]')
        plt.subplot(2, 1, 2)
        plt.semilogy(numpy.median(amplitude, axis=1), 'r')
        plt.axis('tight')
        plt.xlabel('Channels [#]')
        plt.ylabel('Spectrum [arb dBm]')

    h5.close()

# Main body of the script
if __name__ == "__main__":
    parser = OptionParser(usage='python %prog [options] <fbf_file.h5>',
                          version='%prog 0.1a')
    parser.add_option('--nsec',
                      action='store',
                      dest='nsec',
                      type=float,
                      default=1.,
                      help='Number of seconds to read from file for ND characterisation')
    parser.add_option('--verbose',
                      dest='verbose',
                      action='store_true',
                      default=False,
                      help='Show various graphs and output results')
    parser.add_option('--debug',
                      dest='debug',
                      action='store_true',
                      default=False,
                      help='Show verbose output for debugging')
    (opts, args) = parser.parse_args()
    if len(args) < 1:
        raise SystemExit(parser.print_usage())
    filename = args[0]
    if opts.debug:
        opts.nsec = 0.25  # seconds

    # telescope location as observer
    observer = ephem.Observer()
    observer.lon = '21:26:38.0'
    observer.lat = '-30:42:47.4'
    observer.elevation = 1060.0
    observer.epoch = ephem.J2000

    print('\nReading file %s' % (filename,))
    import unpack_fbf_data
    [metadata, adc_clks] = unpack_fbf_data.read_h5(filename, observer, verbose=opts.debug)
    print('Extracting %.1f seconds of data for characterisation' % opts.nsec)
    # characterise the ND behaviour
    characterise_nd(filename, metadata, adc_clks, n_sec=opts.nsec, verbose=opts.debug)

    if opts.verbose or opts.debug:
        try:
            plt.show()
        except:
            pass  # nothing to show

# -fin-
