#!/usr/bin/env python3

#################################################
######## INPUT SHAPER CALIBRATION SCRIPT ########
#################################################
# Derived from the calibrate_shaper.py official Klipper script
# Copyright (C) 2020  Dmitry Butyugin <dmbutyugin@google.com>
# Copyright (C) 2020  Kevin O'Connor <kevin@koconnor.net>
#
# Written by Frix_x#0161 #
# @version: 1.1

# CHANGELOG:
#   v1.1: - improved the damping ratio computation with linear approximation for more precision
#         - reworked the top graph to add more information to it with colored zones,
#           automated peak detection, etc...
#         - added a full spectrogram of the signal on the bottom to allow deeper analysis
#   v1.0: first version of this script inspired from the official Klipper
#         shaper calibration script to add an automatic damping ratio estimation to it


# Be sure to make this script executable using SSH: type 'chmod +x ./graph_shaper.py' when in the folder!

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import optparse, matplotlib, sys, importlib, os, math
from textwrap import wrap
import numpy as np
import matplotlib.pyplot, matplotlib.dates, matplotlib.font_manager
import matplotlib.ticker, matplotlib.gridspec

matplotlib.use('Agg')

MAX_TITLE_LENGTH=65
PEAKS_DETECTION_THRESHOLD=0.05
PEAKS_EFFECT_THRESHOLD=0.12
SPECTROGRAM_LOW_PERCENTILE_FILTER=5


######################################################################
# Computation
######################################################################

# Find the best shaper parameters using Klipper's official algorithm selection
def calibrate_shaper_with_damping(datas, max_smoothing):
    helper = shaper_calibrate.ShaperCalibrate(printer=None)

    calibration_data = helper.process_accelerometer_data(datas[0])
    for data in datas[1:]:
        calibration_data.add_data(helper.process_accelerometer_data(data))

    calibration_data.normalize_to_frequencies()

    shaper, all_shapers = helper.find_best_shaper(calibration_data, max_smoothing, print)

    freqs = calibration_data.freq_bins
    psd = calibration_data.psd_sum
    fr, zeta = compute_damping_ratio(psd, freqs)

    print("Recommended shaper is %s @ %.1f Hz" % (shaper.name, shaper.freq))
    print("Axis has a resonant frequency ω0=%.1fHz with an estimated damping ratio ζ=%.3f" % (fr, zeta))

    return shaper.name, all_shapers, calibration_data, fr, zeta


# Compute damping ratio by using the half power bandwidth method with interpolated frequencies
def compute_damping_ratio(psd, freqs):
    max_power_index = np.argmax(psd)
    fr = freqs[max_power_index]
    max_power = psd[max_power_index]

    half_power = max_power / math.sqrt(2)
    idx_below = np.where(psd[:max_power_index] <= half_power)[0][-1]
    idx_above = np.where(psd[max_power_index:] <= half_power)[0][0] + max_power_index
    freq_below_half_power = freqs[idx_below] + (half_power - psd[idx_below]) * (freqs[idx_below + 1] - freqs[idx_below]) / (psd[idx_below + 1] - psd[idx_below])
    freq_above_half_power = freqs[idx_above - 1] + (half_power - psd[idx_above - 1]) * (freqs[idx_above] - freqs[idx_above - 1]) / (psd[idx_above] - psd[idx_above - 1])

    bandwidth = freq_above_half_power - freq_below_half_power
    zeta = bandwidth / (2 * fr)

    return fr, zeta


def compute_spectrogram(data):
    N = data.shape[0]
    Fs = N / (data[-1,0] - data[0,0])
    # Round up to a power of 2 for faster FFT
    M = 1 << int(.5 * Fs - 1).bit_length()
    window = np.kaiser(M, 6.)
    def _specgram(x):
        return matplotlib.mlab.specgram(
                x, Fs=Fs, NFFT=M, noverlap=M//2, window=window,
                mode='psd', detrend='mean', scale_by_freq=False)

    d = {'x': data[:,1], 'y': data[:,2], 'z': data[:,3]}
    pdata, bins, t = _specgram(d['x'])
    for ax in 'yz':
        pdata += _specgram(d[ax])[0]
    return pdata, bins, t


# This find all the peaks in a curve by looking at when the derivative term goes from positive to negative
# Then only the peaks found above a threshold are kept to avoid capturing peaks in the low amplitude noise of a signal
# An added "virtual" threshold allow me to quantify in an opiniated way the peaks that "could have" effect on the printer
# behavior and are likely known to produce or contribute to the ringing/ghosting in printed parts
def detect_peaks(psd, freqs, window_size=5, vicinity=3):
    # Smooth the curve using a moving average to avoid catching peaks everywhere in noisy signals
    kernel = np.ones(window_size) / window_size
    smoothed_psd = np.convolve(psd, kernel, mode='same')

    # Find peaks on the smoothed curve
    smoothed_peaks = np.where((smoothed_psd[:-2] < smoothed_psd[1:-1]) & (smoothed_psd[1:-1] > smoothed_psd[2:]))[0] + 1
    detection_threshold = PEAKS_DETECTION_THRESHOLD * psd.max()
    effect_threshold = PEAKS_EFFECT_THRESHOLD * psd.max()
    smoothed_peaks = smoothed_peaks[smoothed_psd[smoothed_peaks] > detection_threshold]
 
    # Refine peak positions on the original curve
    refined_peaks = []
    for peak in smoothed_peaks:
        local_max = peak + np.argmax(psd[max(0, peak-vicinity):min(len(psd), peak+vicinity+1)]) - vicinity
        refined_peaks.append(local_max)

    peak_freqs = ["{:.1f}".format(f) for f in freqs[refined_peaks]]

    num_peaks = len(refined_peaks)
    num_peaks_above_effect_threshold = np.sum(psd[refined_peaks] > effect_threshold)
    
    print("Peaks detected on the graph: %d @ %s Hz (%d above effect threshold)" % (num_peaks, ", ".join(map(str, peak_freqs)), num_peaks_above_effect_threshold))

    return np.array(refined_peaks), num_peaks, num_peaks_above_effect_threshold


######################################################################
# Graphing
######################################################################

def plot_freq_response_with_damping(ax, calibration_data, shapers, selected_shaper, fr, zeta, max_freq):
    freqs = calibration_data.freq_bins
    psd = calibration_data.psd_sum[freqs <= max_freq]
    px = calibration_data.psd_x[freqs <= max_freq]
    py = calibration_data.psd_y[freqs <= max_freq]
    pz = calibration_data.psd_z[freqs <= max_freq]
    freqs = freqs[freqs <= max_freq]

    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('x-small')

    ax.set_xlabel('Frequency (Hz)')
    ax.set_xlim([0, max_freq])
    ax.set_ylabel('Power spectral density')
    ax.set_ylim([0, psd.max() + psd.max() * 0.05])

    ax.plot(freqs, psd, label='X+Y+Z', color='purple')
    ax.plot(freqs, px, label='X', color='red')
    ax.plot(freqs, py, label='Y', color='green')
    ax.plot(freqs, pz, label='Z', color='blue')

    ax.xaxis.set_minor_locator(matplotlib.ticker.MultipleLocator(5))
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
    ax.grid(which='major', color='grey')
    ax.grid(which='minor', color='lightgrey')

    ax2 = ax.twinx()
    ax2.set_ylabel('Shaper vibration reduction (ratio)')
    
    best_shaper_vals = None
    no_vibr_shaper = None
    no_vibr_shaper_freq = None
    no_vibr_shaper_accel = 0
    
    # Draw the shappers curves and add their specific parameters in the legend
    # This adds also a way to find the best shaper with 0% of vibrations (to be printed in the legend later)
    for shaper in shapers:
        shaper_max_accel = round(shaper.max_accel / 100.) * 100.
        label = "%s (%.1f Hz, vibr=%.1f%%, sm~=%.2f, accel<=%.f)" % (
                shaper.name.upper(), shaper.freq,
                shaper.vibrs * 100., shaper.smoothing,
                shaper_max_accel)
        linestyle = 'dotted'
        if shaper.name == selected_shaper:
            linestyle = 'dashdot'
            selected_shaper_freq = shaper.freq
            best_shaper_vals = shaper.vals
        if (shaper.vibrs * 100 == 0.) and (shaper_max_accel > no_vibr_shaper_accel):
            no_vibr_shaper_accel = shaper_max_accel
            no_vibr_shaper = shaper.name
            no_vibr_shaper_freq = shaper.freq
        ax2.plot(freqs, shaper.vals, label=label, linestyle=linestyle)
    ax.plot(freqs, psd * best_shaper_vals, label='With %s applied' % (selected_shaper.upper()), color='cyan')

    # Draw the detected peaks and name them
    # This also draw the detection threshold and warning threshold (aka "effect zone")
    peaks, _, _ = detect_peaks(psd, freqs)
    peaks_warning_threshold = PEAKS_DETECTION_THRESHOLD * psd.max()
    peaks_effect_threshold = PEAKS_EFFECT_THRESHOLD * psd.max()
    
    ax.plot(freqs[peaks], psd[peaks], "x", color='black', label='Detected peaks', markersize=8)
    for idx, peak in enumerate(peaks):
        if psd[peak] > peaks_effect_threshold:
            fontcolor = 'red'
            fontweight = 'bold'
        else:
            fontcolor = 'black'
            fontweight = 'normal'
        ax.annotate(f"{idx+1}", (freqs[peak], psd[peak]), 
                    textcoords="offset points", xytext=(8, 5), 
                    ha='left', fontsize=14, color=fontcolor, weight=fontweight)
    ax.axhline(y=peaks_warning_threshold, color='black', linestyle='--', linewidth=0.5)
    ax.axhline(y=peaks_effect_threshold, color='black', linestyle='--', linewidth=0.5)
    ax.fill_between(freqs, 0, peaks_warning_threshold, color='green', alpha=0.15, label='Relax Region')
    ax.fill_between(freqs, peaks_warning_threshold, peaks_effect_threshold, color='orange', alpha=0.2, label='Warning Region')

    # Final user recommendations added to the legend with an added 0% vibration shaper and the estimated damping ratio over stock Klipper's algorithms
    ax2.plot([], [], ' ', label="Recommended shaper: %s @ %.1f Hz" % (selected_shaper.upper(), selected_shaper_freq))
    ax2.plot([], [], ' ', label="Recommended low vibrations shaper: %s @ %.1f Hz" % (no_vibr_shaper.upper(), no_vibr_shaper_freq))
    ax2.plot([], [], ' ', label="Estimated damping ratio (ζ): %.3f" % (zeta))

    # Add the main resonant frequency and damping ratio of the axis to the graph title
    ax.set_title("Axis Frequency Profile (ω0=%.1fHz, ζ=%.3f)" % (fr, zeta), fontsize=14)
    ax.legend(loc='upper left', prop=fontP)
    ax2.legend(loc='upper right', prop=fontP)

    return freqs[peaks]


# Plot a time-frequency spectrogram to see how the system respond over time during the
# resonnance test. This can highlight hidden spots from the standard PSD graph from other harmonics
def plot_spectrogram(ax, data, peaks, max_freq):
    pdata, bins, t = compute_spectrogram(data)

    # We need to normalize the data to get a proper signal on the spectrogram
    # However, while using "LogNorm" provide too much background noise, using
    # "Normalize" make only the resonnance appearing and hide interesting elements
    # So we need to filter out the lower part of the data (ie. find the proper vmin for LogNorm)
    vmin_value = np.percentile(pdata, SPECTROGRAM_LOW_PERCENTILE_FILTER)

    ax.set_title("Time-Frequency Spectrogram", fontsize=14)
    ax.pcolormesh(bins, t, pdata.T, norm=matplotlib.colors.LogNorm(vmin=vmin_value),
                  cmap='inferno', shading='gouraud')

    # Add peaks lines in the spectrogram to get hint from peaks found in the first graph
    if peaks is not None:
        for idx, peak in enumerate(peaks):
            ax.axvline(peak, color='cyan', linestyle='dotted', linewidth=0.75)
            ax.annotate(f"Peak {idx+1}", (peak, t[-1]*0.9), 
                        textcoords="data", color='cyan', rotation=90, fontsize=12,
                        verticalalignment='top', horizontalalignment='right')

    ax.set_xlim([0., max_freq])
    ax.set_ylabel('Time (s)')
    ax.set_xlabel('Frequency (Hz)')

    return


######################################################################
# Startup and main routines
######################################################################

def parse_log(logname):
    with open(logname) as f:
        for header in f:
            if not header.startswith('#'):
                break
        if not header.startswith('freq,psd_x,psd_y,psd_z,psd_xyz'):
            # Raw accelerometer data
            return np.loadtxt(logname, comments='#', delimiter=',')
    # Power spectral density data or shaper calibration data
    raise ValueError("File %s does not contain raw accelerometer data and therefore "
               "is not supported by this script. Please use the official Klipper "
               "calibrate_shaper.py script to process it instead." % (logname,))


def setup_klipper_import(kdir):
    global shaper_calibrate
    kdir = os.path.expanduser(kdir)
    sys.path.append(os.path.join(kdir, 'klippy'))
    shaper_calibrate = importlib.import_module('.shaper_calibrate', 'extras')


def shaper_calibration(lognames, klipperdir="~/klipper", max_smoothing=None, max_freq=200.):
    setup_klipper_import(klipperdir)

    # Parse data
    datas = [parse_log(fn) for fn in lognames]

    # Calibrate shaper and generate outputs
    selected_shaper, shapers, calibration_data, fr, zeta = calibrate_shaper_with_damping(datas, max_smoothing)

    fig = matplotlib.pyplot.figure()
    gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[4, 3])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    fig.suptitle("\n".join(wrap(
        "Input Shaper calibration (%s)" % (', '.join(lognames)), MAX_TITLE_LENGTH)), fontsize=16)

    peaks = plot_freq_response_with_damping(ax1, calibration_data, shapers, selected_shaper, fr, zeta, max_freq)
    plot_spectrogram(ax2, datas[0], peaks, max_freq)

    fig.set_size_inches(10, 12)
    fig.tight_layout()
    fig.subplots_adjust(top=0.93)

    return fig


def main():
    # Parse command-line arguments
    usage = "%prog [options] <logs>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-o", "--output", type="string", dest="output",
                    default=None, help="filename of output graph")
    opts.add_option("-f", "--max_freq", type="float", default=200.,
                    help="maximum frequency to graph")
    opts.add_option("-s", "--max_smoothing", type="float", default=None,
                    help="maximum shaper smoothing to allow")
    opts.add_option("-k", "--klipper_dir", type="string", dest="klipperdir",
                    default="~/klipper", help="main klipper directory")
    options, args = opts.parse_args()
    if len(args) < 1:
        opts.error("Incorrect number of arguments")
    if options.output is None:
        opts.error("You must specify an output file.png to use the script (option -o)")
    if options.max_smoothing is not None and options.max_smoothing < 0.05:
        opts.error("Too small max_smoothing specified (must be at least 0.05)")

    fig = shaper_calibration(args, options.klipperdir, options.max_smoothing, options.max_freq)
    fig.savefig(options.output)


if __name__ == '__main__':
    main()
