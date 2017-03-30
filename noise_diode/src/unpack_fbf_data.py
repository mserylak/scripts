# Copyright (C) 2016 by Maciej Serylak
# Licensed under the Academic Free License version 3.0
# This program comes with ABSOLUTELY NO WARRANTY.
# You are free to modify and redistribute this code as long
# as you do not remove the above attribution and reasonably
# inform recipients that you have modified the original work.
# https://github.com/mserylak/scripts/blob/master/prepareH5.py
#
# Modified by Bruce Merry
# https://github.com/mserylak/scripts/blob/master/fastH5.py
# Modified by Ruby van Rooyen

import platform
print('Python %s' % platform.python_version())
import sys
python_version = sys.version_info.major

from datetime import datetime
from numba import jit
from optparse import OptionParser, OptionGroup
import ephem
import h5py
import numba
import numpy
import struct


# Read raw FBF.h5 file
def read_h5(
        filename,
        observer,
        verbose=False,
        ):

    metadata = {}

    h5 = h5py.File(filename, 'r')

    if verbose:
        for group_name in h5:
            print(group_name)
            for dataset_name in h5[group_name]:
                print(dataset_name)
            print

    # read timestamps
    metadata['ts_type'] = h5['Data/timestamps'].attrs['timestamp_type']
    if verbose:
        print('Get %s timestamps from file' % metadata['ts_type'])
    clockcounts = h5['Data/timestamps'][:]
    if verbose:
        print('Read %d timestamps' % len(clockcounts))

    # difference between adc_counts to check for missing packets
    nts_adc_snapblock = numpy.diff(clockcounts)[0]  # all should be 8192
    metadata['nsamples'] = nts_adc_snapblock
    if verbose:
        print('Nr time samples per ADC snap block = %d' % nts_adc_snapblock)
    if (numpy.where(numpy.diff(clockcounts) != nts_adc_snapblock)[0].size) > 0:
        print('Missing spectra in: %s' % (filename))
        print(numpy.where(numpy.diff(clockcounts) != nts_adc_snapblock)[0])
        raise RuntimeError('Missing spectra')

    # read data, assume layout (n_chans, n_timestamps, n_complex)
    metadata['rawdata'] = 'Data/bf_raw'
    rawdata = h5['Data/bf_raw']
    if verbose:
        print('Reading raw data from file')
    # do some checks
    [n_chans, n_ts, n_c] = rawdata.shape
    metadata['nchannels'] = n_chans
    metadata['nspectra'] = n_ts
    if abs(n_ts-len(clockcounts)) > 0:
        raise RuntimeError('Not expected data format: Nr timestamps do not match')  # noqa
    if abs(n_chans-int(h5['TelescopeModel/cbf'].attrs['n_chans'])) > 0:
        raise RuntimeError('Not expected data format: Nr channels do not match')  # noqa

    scale_factor_timestamp = float(h5['TelescopeModel/cbf'].attrs['scale_factor_timestamp'])  # noqa
    tot_ts = clockcounts[-1] - clockcounts[0]
    n_sec = float(tot_ts)/scale_factor_timestamp
    sps = int(tot_ts/n_sec)
    metadata['clks_per_sec'] = n_ts/n_sec
    metadata['fs'] = sps

    metadata['clk_sync'] = h5['/TelescopeModel/cbf'].attrs['sync_time']
    metadata['cenfreq'] = h5['TelescopeModel/cbf'].attrs['center_freq']
    metadata['bandwidth'] = h5['TelescopeModel/cbf'].attrs['bandwidth']

    observer.temp = h5['TelescopeModel/anc/air_temperature'][0]['value']
    observer.pressure = h5['TelescopeModel/anc/air_pressure'][0]['value']
    observer.horizon = numpy.radians(15)
    # antenna specific metadata
    ants = [str(key) for key in h5['TelescopeModel'].keys() if 'm0' in key]
    metadata['ants'] = ants
    for ant in ants:
        metadata[ant] = {}
        metadata[ant]['target'] = h5['TelescopeModel'][ant]['target'][0]['value']
        metadata[ant]['az'] = h5['TelescopeModel'][ant]['pos_actual_scan_azim'][0]['value']
        metadata[ant]['el'] = h5['TelescopeModel'][ant]['pos_actual_scan_elev'][0]['value']
        observer.date = datetime.utcfromtimestamp(h5['TelescopeModel'][ant]['pos_actual_scan_azim'][0]['timestamp'])
        ra, dec = observer.radec_of(numpy.radians(metadata[ant]['az']), numpy.radians(metadata[ant]['el']))
        metadata[ant]['ra'] = str(ra)
        metadata[ant]['dec'] = str(dec)

    h5.close()
    return [metadata, clockcounts]


# Functions used in SIGPROC header creation
def _write_string(key, value):
    return "".join([struct.pack("I", len(key)), key, struct.pack("I", len(value)), value])


def _write_int(key, value):
    return "".join([struct.pack("I", len(key)), key, struct.pack("I", value)])


def _write_double(key, value):
    return "".join([struct.pack("I", len(key)), key, struct.pack("d", value)])


def _write_char(key, value):
    return "".join([struct.pack("I", len(key)), key, struct.pack("b", value)])


# Visibility products packaging for older python versions
def np_to_stokesI(x, y):
    x_r = numpy.asarray(x[..., 0], dtype=numpy.float32)
    x_i = numpy.asarray(x[..., 1], dtype=numpy.float32)
    y_r = numpy.asarray(y[..., 0], dtype=numpy.float32)
    y_i = numpy.asarray(y[..., 1], dtype=numpy.float32)
    out = x_r * x_r + x_i * x_i + y_r * y_r + y_i * y_i
    return out


# Stokes parameters
# I = abs(Ex)^2 + abs(Ey)^2
# Q = abs(Ex)^2 - abs(Ey)^2
# U = 2Re(ExEy*)^2
# V = 2Im(ExEy*)^2
def np_to_stokes(x, y, fullstokes=False):
    x_r = numpy.asarray(x[..., 0], dtype=numpy.float32)
    x_i = numpy.asarray(x[..., 1], dtype=numpy.float32)
    y_r = numpy.asarray(y[..., 0], dtype=numpy.float32)
    y_i = numpy.asarray(y[..., 1], dtype=numpy.float32)
    xx = x_r * x_r + x_i * x_i
    yy = y_r * y_r + y_i * y_i
    xy_r = x_r * y_r + x_i * y_i
    xy_i = x_i * y_r - x_r * y_i
    if fullstokes:
        out = numpy.dstack((xx + yy, xx - yy, 2 * xy_r, 2 * xy_i)).swapaxes(1, 2)
    else:
        out = numpy.dstack((xx, yy, xy_r, xy_i)).swapaxes(1, 2)
    return out


# Visibility products packaging
# @jit(nopython=True)
def _to_stokesI(x, y, decimation_factor, out):
    for i in range(out.shape[1]):
        for j in range(out.shape[0]):
            s = numpy.float32(0)
            for k in range(j * decimation_factor, (j + 1) * decimation_factor):
                x_r = numpy.float32(x[i, k, 0])
                x_i = numpy.float32(x[i, k, 1])
                y_r = numpy.float32(y[i, k, 0])
                y_i = numpy.float32(y[i, k, 1])
                s += x_r * x_r + x_i * x_i + y_r * y_r + y_i * y_i
            out[j, i] = s / decimation_factor


def to_stokesI(x, y, decimation_factor):
    out = numpy.zeros((x.shape[1] // decimation_factor, x.shape[0]), numpy.float32)
    _to_stokesI(x, y, decimation_factor, out)
    return out


# @jit(nopython=True)
def _to_stokes(x, y, out, fullstokes=False):
    for i in range(x.shape[0]):
        for j in range(x.shape[1]):
            x_r = numpy.float32(x[i, j, 0])
            x_i = numpy.float32(x[i, j, 1])
            y_r = numpy.float32(y[i, j, 0])
            y_i = numpy.float32(y[i, j, 1])
            xx = x_r * x_r + x_i * x_i
            yy = y_r * y_r + y_i * y_i
            xy_r = x_r * y_r + x_i * y_i
            xy_i = x_i * y_r - x_r * y_i
            if fullstokes:
                out[i, 0, j] = xx + yy
                out[i, 1, j] = xx - yy
                out[i, 2, j] = 2 * xy_r
                out[i, 3, j] = 2 * xy_i
            else:
                out[i, 0, j] = xx
                out[i, 1, j] = yy
                out[i, 2, j] = xy_r
                out[i, 3, j] = xy_i


def to_stokes(x, y, fullstokes=False):
    out = numpy.empty((x.shape[0], 4, x.shape[1]), numpy.float32)
    _to_stokes(x, y, out, fullstokes=fullstokes)
    return out


# Main body of the script
if __name__ == "__main__":

    parser = OptionParser(usage='python %prog [options] <fbf_file_polA.h5> [fbf_file_polB.h5]',
                          version='%prog 0.1a')
    # increase space reserved for option flags (default 24), trick to make the help more readable
    parser.formatter.max_help_position = 100
    # increase help width from 120 to 200
    parser.formatter.width = 250
    group = OptionGroup(parser, 'Telescope Geographic Coordinates')
    group.add_option('--lat',
                     action='store',
                     dest='lat',
                     type=str,
                     default='-30:42:47.4',
                     help="Latitude (default MeerKAT lat='%default')")
    group.add_option('--lon',
                     action='store',
                     dest='lon',
                     type=str,
                     default='21:26:38.0',
                     help="Longitude (default MeerKAT lon='%default')")
    group.add_option('--alt',
                     action='store',
                     dest='alt',
                     type=float,
                     default=1060.0,
                     help="Altitude (default MeerKAT alt='%default')")
    parser.add_option_group(group)
    parser.add_option('--chunk',
                      action='store',
                      type=int,
                      dest='chunk_size',
                      default=256,
                      help='Process chunks from large HDF5 files (default chunk size=%default)')
    parser.add_option('--ndec',
                      action='store',
                      type=int,
                      dest='decimation_factor',
                      default=1,
                      help='Factor to decimate/downsample with (default %default)')
    parser.add_option('--out',
                      action='store',
                      type=str,
                      dest='out_file',
                      default='out.fil',
                      help='Give output filename (default %default).')
    parser.add_option('--stokesI',
                      dest='stokesI',
                      action='store_true',
                      help='Output only Stoke I')
    parser.add_option('--stokes',
                      dest='full_stokes',
                      action='store_true',
                      help='Output Stokes vector [I, Q, U, V]')
    parser.add_option('--vis',
                      dest='coherence_vis',
                      action='store_true',
                      help='Default output coherence vector [AA*, BB*, Re(AB*), Im(AB*)]')
    parser.add_option('--no_opt',
                      dest='no_opt',
                      action='store_true',
                      help='Switch off calculation optimization when this functionality not available')
    group = OptionGroup(parser, 'Additional Output Options')
    group.add_option('--verbose',
                     dest='verbose',
                     action='store_true',
                     default=False,
                     help='Show various parameters and results')
    group.add_option('--debug',
                     dest='debug',
                     action='store_true',
                     default=False,
                     help='Show very verbose output for debugging')
    parser.add_option_group(group)
    (opts, args) = parser.parse_args()

    if len(args) < 1:
        raise SystemExit(parser.print_usage())
    if len(args) > 2:
        print('Cannot handle more than 2 polarisations')
        raise SystemExit(parser.print_usage())

    if opts.verbose or opts.debug:
        verbose = True

    if not opts.stokesI and not opts.full_stokes and not opts.coherence_vis:
        opts.coherence_vis = True
    elif opts.stokesI:
        opts.full_stokes = False
        opts.coherence_vis = False
    elif opts.full_stokes:
        opts.stokesI = False
        opts.coherence_vis = False

    chunk_size = opts.chunk_size
    decimation_factor = opts.decimation_factor
    if verbose:
        print('chunkSize: %d' % chunk_size)
        print('decimationFactor: %d' % decimation_factor)
    # check if decimation_factor is power of two, if not then quit.
    if(decimation_factor != 0 and ((decimation_factor & (decimation_factor - 1)) == 0) is False):
        print('Input error!  decimationFactor not a power of two!')
        raise SystemExit()
    # check if decimation_factor is greater than chunk_size.
    if (decimation_factor > chunk_size):
        chunk_size = 2 * decimation_factor
        print('new chunkSize: %d' % chunk_size)

    # telescope location as observer
    observer = ephem.Observer()
    observer.lon = opts.lon
    observer.lat = opts.lat
    observer.elevation = opts.alt
    observer.epoch = ephem.J2000

    beamformer = {}
    for idx, filename in enumerate(args):
        key = 'pol_%d' % idx
        print('Reading file %s into %s' % (filename, key))
        [metadata, adc_clks] = read_h5(filename, observer, verbose=opts.debug)
        beamformer[key] = {
                            'h5file': filename,
                            'metadata': metadata,
                            'adc_clks': adc_clks,
                          }
    if idx < 1:
        beamformer['pol_1'] = beamformer['pol_0'].copy()

    # verify parameters that should be the same for observations on both pol files
    ants = beamformer['pol_0']['metadata']['ants']
    if len(ants) > 1:
        raise SystemExit('More than 1 antenna: Complete implementation before proceding')
    source_name = beamformer['pol_0']['metadata'][ants[0]]['target']
    right_ascension = beamformer['pol_0']['metadata'][ants[0]]['ra']
    declination = beamformer['pol_0']['metadata'][ants[0]]['dec']
    if verbose:
        print('sourceName: %s' % source_name)
        print('rightAscension: %s' % right_ascension)
        print('declination: %s' % declination)

    # basic verification between files of the 2 polarisations
    if (beamformer['pol_0']['metadata']['fs'] != beamformer['pol_1']['metadata']['fs']):
        raise RuntimeError('Files have different sample rates')
    sample_rate = beamformer['pol_0']['metadata']['fs']  # sps
    if verbose:
        print('samplingClock: %.f Hz' % sample_rate)

    if (beamformer['pol_0']['metadata']['nchannels'] != beamformer['pol_1']['metadata']['nchannels']):
        print('Number of channels differs between the polarizations.')
        raise RuntimeError('channelNumberPol0 %d != channelNumberPol1 %d' %
                          (beamformer['pol_0']['metadata']['nchannels'], beamformer['pol_1']['metadata']['nchannels']))
    nchannels = beamformer['pol_0']['metadata']['nchannels']
    if verbose:
        print('complexChannels: %d' % nchannels)

    # find UTC sync time for data files
    if (beamformer['pol_0']['metadata']['clk_sync'] != beamformer['pol_1']['metadata']['clk_sync']):
        print('System sync timestamp differ between the polarizations.')
        raise RuntimeError()
    sync_ts = beamformer['pol_0']['metadata']['clk_sync']
    if verbose:
        print('syncTime: %d' % sync_ts)

    if (beamformer['pol_0']['metadata']['nsamples'] != beamformer['pol_1']['metadata']['nsamples']):
        print('Number of channels differs between the polarizations.')
        raise RuntimeError('channelNumberPol0 %d != channelNumberPol1 %d' %
                          (beamformer['pol_0']['metadata']['nsamples'], beamformer['pol_1']['metadata']['nsamples']))
    nsamples = beamformer['pol_0']['metadata']['nsamples']
    if verbose:
        print('ADCsnapblock: %d' % nsamples)

    sample_interval = nsamples / sample_rate
    if (decimation_factor > 1):
        sample_interval = float(sample_interval) * float(decimation_factor)
    if verbose:
        print('Nyquist sample_interval: %.20f s' % sample_interval)
        print('samplingTime: %.20f ms' % (sample_interval*1e6))

    # calculating where both files start overlapping
    start_sync_ts = numpy.max([beamformer['pol_0']['adc_clks'][0], beamformer['pol_1']['adc_clks'][0]])
    start_sync_ts_polA = numpy.where(beamformer['pol_0']['adc_clks'] == start_sync_ts)[0][0]
    start_sync_ts_polB = numpy.where(beamformer['pol_1']['adc_clks'] == start_sync_ts)[0][0]
    if verbose:
        print('countADCPol0[0]: %d' % beamformer['pol_0']['adc_clks'][0])
        print('countADCPol1[0]: %d' % beamformer['pol_1']['adc_clks'][0])
        print('Sync to start timestamp: %d' % start_sync_ts)
        print('\tStart timestamp polA[%d]: %d' % (start_sync_ts_polA, beamformer['pol_0']['adc_clks'][start_sync_ts_polA]))
        print('\tStart timestamp polB[%d]: %d' % (start_sync_ts_polB, beamformer['pol_1']['adc_clks'][start_sync_ts_polB]))
        print('countADCPol0[%d]: %d' % (start_sync_ts_polA, beamformer['pol_0']['adc_clks'][start_sync_ts_polA]))
        print('countADCPol1[%d]: %d' % (start_sync_ts_polB, beamformer['pol_1']['adc_clks'][start_sync_ts_polB]))
        print('startSyncADC: %d' % start_sync_ts)

  # calculating where both files end overlaping
    end_sync_ts = numpy.min([beamformer['pol_0']['adc_clks'][-1], beamformer['pol_1']['adc_clks'][-1]])
    end_sync_ts_polA = numpy.where(beamformer['pol_0']['adc_clks'] == end_sync_ts)[0][0]
    end_sync_ts_polB = numpy.where(beamformer['pol_1']['adc_clks'] == end_sync_ts)[0][0]
    if verbose:
        print('countADCPol0[-1]: %d' % beamformer['pol_0']['adc_clks'][-1])
        print('countADCPol1[-1]: %d' % beamformer['pol_1']['adc_clks'][-1])
        print('Sync to end timestamp: %d' % end_sync_ts)
        print('\tEnd timestamp polA[%d]: %d' % (end_sync_ts_polA, beamformer['pol_0']['adc_clks'][end_sync_ts_polA]))
        print('\tEnd timestamp polB[%d]: %d' % (end_sync_ts_polB, beamformer['pol_1']['adc_clks'][end_sync_ts_polB]))
        print('countADCPol0[%d]: %d' % (end_sync_ts_polA, beamformer['pol_0']['adc_clks'][end_sync_ts_polA]))
        print('countADCPol1[%d]: %d' % (end_sync_ts_polB, beamformer['pol_1']['adc_clks'][end_sync_ts_polB]))
        print('endSyncADC: %d' % end_sync_ts)

    # observation metadata -- sampling times, start MJD times, frequencies etc.
    start_ts = start_sync_ts / sample_rate
    unix_start_ts = float(sync_ts) + start_ts
    unix_dt = datetime.utcfromtimestamp(unix_start_ts).strftime('%Y-%m-%d %H:%M:%S.%f')
    start_mjd = ephem.julian_date(ephem.Date(unix_dt)) - 2400000.5  # convert to MJD
    cen_freq = beamformer['pol_0']['metadata']['cenfreq']
    bandwidth = beamformer['pol_0']['metadata']['bandwidth']
    channel_bw = bandwidth/nchannels
    if verbose:
        print('obsStartTime: %.12f' % start_ts)
        print('obsSyncDate: %s' % unix_dt)
        print('startTimeMJD: %.12f' % start_mjd)
        print('freqCent: %f' % cen_freq)
        print('channelBW: %.10f MHz' % (channel_bw*1e-6))

    # upper_freq = cen_freq + bandwidth/2. - channel_bw/2.
    upper_freq = cen_freq + bandwidth/2.
    # lower_freq = cen_freq - bandwidth/2.+ channel_bw/2.
    lower_freq = cen_freq - bandwidth/2.
    # Getting number of spectra from each file.
    nspectra_polA = beamformer['pol_0']['metadata']['nspectra']
    nspectra_polB = beamformer['pol_1']['metadata']['nspectra']
    if verbose:
        print('freqTop: %.10f MHz' % (upper_freq*1e-6))
        print('freqBottom: %.10f MHz' % (lower_freq*1e-6))
        print('spectraNumberPol0: %d' % nspectra_polA)
        print('spectraNumberPol1: %d' % nspectra_polB)

# discussion
    # print
    # samplingClock = 1712.0e6
    # # print ("samplingClock: %.f Hz") % samplingClock
    # complexChannels = 8192.0
    # # print ("complexChannels: %f") % complexChannels
    # channelBW = (samplingClock / complexChannels) * 1e-6
    # print ("channelBW: %.10f MHz") % channelBW
    # freqTop = cen_freq*1e-6 + (((nchannels / 2) - 1) * channelBW)
    # print ("freqTop: %f") % freqTop
    # freqBottom = cen_freq*1e-6 - (((nchannels / 2)) * channelBW)
    # print ("freqBottom: %f") % freqBottom
# discussion

# discussion -- need to add some comments
    print('outFileName: %s' % opts.out_file)
    # Creating and populating file header.
    fileOut = open(opts.out_file, 'wab')
    start_header = 'HEADER_START'
    header = ''.join([struct.pack('I', len(start_header)), start_header])
    header = ''.join([header, _write_string('source_name', source_name)])
    header = ''.join([header, _write_int('machine_id', 13)])
    header = ''.join([header, _write_int('telescope_id', 64)])
    header = ''.join([header, _write_double('src_raj', float(right_ascension.replace(':', '')))])
    header = ''.join([header, _write_double('src_dej', float(declination.replace(':', '')))])
    header = ''.join([header, _write_int('data_type', 1)])
    header = ''.join([header, _write_double('fch1', lower_freq)])
    header = ''.join([header, _write_double('foff', channel_bw)])
    header = ''.join([header, _write_int('nchans', nchannels)])
    header = ''.join([header, _write_int('nbits', 32)])
    header = ''.join([header, _write_double('tstart', start_mjd)])
    header = ''.join([header, _write_double('tsamp', sample_interval)])
    if opts.coherence_vis or opts.full_stokes:
      header = ''.join([header, _write_int('nifs', 4)])
    else:
      header = ''.join([header, _write_int('nifs', 1)])
    end_header = 'HEADER_END'
    header = ''.join([header, struct.pack('I', len(end_header)), end_header])
    fileOut.write(header)

    # Extracting data from h5 files and writing to filterbank file.
    # Chunking in HDF5
    # https://support.hdfgroup.org/HDF5/doc/Advanced/Chunking/index.html
    # http://stackoverflow.com/questions/12264309/statistics-on-huge-numpy-hdf5-arrays
    # Numpy works by loading all the data into the memory, so won't be able to load naively the data.
    # Divide the problem into chunks, and use a map/reduce approach
    nts_polA = end_sync_ts_polA - start_sync_ts_polA
    nts_polB = end_sync_ts_polB - start_sync_ts_polB
    if numpy.abs(nts_polA - nts_polB) > 0:
        raise RuntimeError('Different number timestamps between polarisation, build in procedures to handle spectra loss')
    # build a mask that has false for missing spectra in either file to avoid reading it in both
    nts_sync = chunk_size*(nts_polA/chunk_size)
    nts_cnt = nts_polA/chunk_size
    if verbose:
        import time
        etime = time.time()
    h5_polA = h5py.File(args[0], 'r')
    h5_polB = h5py.File(args[1], 'r')
    for cnt in range(nts_cnt):
        if opts.debug:
            print('%d of %d' % (cnt+1, nts_cnt))
        # select a chunk size (according to memory constraints)
        ts_step = cnt*chunk_size
        # divide the data in chunks of this size (either by creating several files, or by loading only one chunk at a time)
        spectra_chunk_polA = h5_polA['Data/bf_raw'][:, (start_sync_ts_polA + ts_step):(start_sync_ts_polA + ts_step + chunk_size), :]
        if opts.debug:
            print('Reading A pol took %.3f secs' % (time.time()-etime))
        spectra_chunk_polB = h5_polB['Data/bf_raw'][:, (start_sync_ts_polB + ts_step):(start_sync_ts_polB + ts_step + chunk_size), :]
        if opts.debug:
            print('Reading B pol took %.3f secs' % (time.time()-etime))
        # for each chunk, do the computation and unload the data
        if opts.stokesI:
            if opts.no_opt:
                stokesI = to_stokesI(spectra_chunk_polA, spectra_chunk_polB, decimation_factor)
                stokesI = numpy.require(stokesI, numpy.float32, requirements='C')
                stokesI.tofile(fileOut)
            else:
                stokesI = np_to_stokesI(spectra_chunk_polA, spectra_chunk_polB)
                stokesI = stokesI.reshape(-1, (chunk_size / decimation_factor), decimation_factor).mean(axis=2)
                # python2.7 don't have tobytes()
                if python_version > 2:
                    bytesStokesI_float32 = stokesI.T.astype(numpy.float32).tobytes(order='C')
                else:
                    bytesStokesI_float32 = stokesI.T.astype(numpy.float32).tostring(order='C')
                fileOut.write(bytesStokesI_float32)
            if opts.debug:
                print('Calculating stokesI took %.3f secs' % (time.time()-etime))
        else:
            if opts.no_opt:
                stokesIQUV = to_stokes(spectra_chunk_polA, spectra_chunk_polB, fullstokes=opts.full_stokes)
            else:
                stokesIQUV = np_to_stokes(spectra_chunk_polA, spectra_chunk_polB, fullstokes=opts.full_stokes)
            if (decimation_factor > 1):
                stokesIQUV = stokesIQUV.reshape(-1, 4, (chunk_size / decimation_factor), decimation_factor).mean(axis=3)
            # python2.7 don't have tobytes()
            if python_version > 2:
                bytesStokesIQUV_float32 = stokesIQUV.T.astype(numpy.float32).tobytes(order='C')
            else:
                bytesStokesIQUV_float32 = stokesIQUV.T.astype(numpy.float32).tostring(order='C')
            fileOut.write(bytesStokesIQUV_float32)
            if opts.debug:
                print('Calculating stokes took %.3f secs' % (time.time()-etime))
    # [optional] merge the results into your final result
    h5_polA.close()
    h5_polB.close()
    if verbose:
        print('Processing %d chunks took %.3f secs' % (nts_cnt, time.time()-etime))

    fileOut.close()

# -fin-
