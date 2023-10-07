#!/usr/bin/env python3

#################################################
######## CoreXY BELTS CALIBRATION SCRIPT ########
#################################################
# Written by Frix_x#0161 #
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of this tool for enhanced vizualisation of belt graphs


# Be sure to make this script executable using SSH: type 'chmod +x ./graph_belts.py' when in the folder!

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import optparse, matplotlib, sys, importlib, os
from textwrap import wrap
from collections import namedtuple
import numpy as np
import matplotlib.pyplot, matplotlib.dates, matplotlib.font_manager
import matplotlib.ticker, matplotlib.gridspec, matplotlib.colors
import matplotlib.patches

matplotlib.use('Agg')

MAX_TITLE_LENGTH = 65
ALPHABET = "ABCDEFGHIJKLMNOPQRSTUVWXYZ" # For paired peaks names

PEAKS_DETECTION_THRESHOLD = 0.20
CURVE_SIMILARITY_SIGMOID_K = 0.6
DC_GRAIN_OF_SALT_FACTOR = 0.75
DC_THRESHOLD_METRIC = 1.5e9
DC_MAX_UNPAIRED_PEAKS_ALLOWED = 4

# Define the SignalData namedtuple
SignalData = namedtuple('CalibrationData', ['freqs', 'psd', 'peaks', 'paired_peaks', 'unpaired_peaks'])


######################################################################
# Computation of the PSD graph
######################################################################

# Calculate estimated "power spectral density" using existing Klipper tools
def calc_freq_response(data):
    helper = shaper_calibrate.ShaperCalibrate(printer=None)
    return helper.process_accelerometer_data(data)


# Calculate or estimate a "similarity" factor between two PSD curves and scale it to a percentage. This is
# used here to quantify how close the two belts path behavior and responses are close together.
def compute_curve_similarity_factor(signal1, signal2):
    freqs1 = signal1.freqs
    psd1 = signal1.psd
    freqs2 = signal2.freqs
    psd2 = signal2.psd
    
    # Interpolate PSDs to match the same frequency bins and do a cross-correlation
    psd2_interp = np.interp(freqs1, freqs2, psd2)
    cross_corr = np.correlate(psd1, psd2_interp, mode='full')
    
    # Find the peak of the cross-correlation and compute a similarity normalized by the energy of the signals
    peak_value = np.max(cross_corr)
    similarity = peak_value / (np.sqrt(np.sum(psd1**2) * np.sum(psd2_interp**2)))

    # Apply sigmoid scaling to get better numbers and get a final percentage value
    scaled_similarity = sigmoid_scale(-np.log(1 - similarity), CURVE_SIMILARITY_SIGMOID_K)
    
    return scaled_similarity


# This find all the peaks in a curve by looking at when the derivative term goes from positive to negative
# Then only the peaks found above a threshold are kept to avoid capturing peaks in the low amplitude noise of a signal
def detect_peaks(psd, freqs, window_size=5, vicinity=3):
    # Smooth the curve using a moving average to avoid catching peaks everywhere in noisy signals
    kernel = np.ones(window_size) / window_size
    smoothed_psd = np.convolve(psd, kernel, mode='same')
    
    # Find peaks on the smoothed curve
    smoothed_peaks = np.where((smoothed_psd[:-2] < smoothed_psd[1:-1]) & (smoothed_psd[1:-1] > smoothed_psd[2:]))[0] + 1
    detection_threshold = PEAKS_DETECTION_THRESHOLD * psd.max()
    smoothed_peaks = smoothed_peaks[smoothed_psd[smoothed_peaks] > detection_threshold]
    
    # Refine peak positions on the original curve
    refined_peaks = []
    for peak in smoothed_peaks:
        local_max = peak + np.argmax(psd[max(0, peak-vicinity):min(len(psd), peak+vicinity+1)]) - vicinity
        refined_peaks.append(local_max)
    
    return np.array(refined_peaks), freqs[refined_peaks]


# This function create pairs of peaks that are close in frequency on two curves (that are known
# to be resonances points and must be similar on both belts on a CoreXY kinematic)
def pair_peaks(peaks1, freqs1, psd1, peaks2, freqs2, psd2):
    # Compute a dynamic detection threshold to filter and pair peaks efficiently
    # even if the signal is very noisy (this get clipped to a maximum of 10Hz diff)
    distances = []
    for p1 in peaks1:
        for p2 in peaks2:
            distances.append(abs(freqs1[p1] - freqs2[p2]))
    distances = np.array(distances)
    
    median_distance = np.median(distances)
    iqr = np.percentile(distances, 75) - np.percentile(distances, 25)
    
    threshold = median_distance + 1.5 * iqr
    threshold = min(threshold, 10)
    
    # Pair the peaks using the dynamic thresold
    paired_peaks = []
    unpaired_peaks1 = list(peaks1)
    unpaired_peaks2 = list(peaks2)
    
    while unpaired_peaks1 and unpaired_peaks2:
        min_distance = threshold + 1
        pair = None
        
        for p1 in unpaired_peaks1:
            for p2 in unpaired_peaks2:
                distance = abs(freqs1[p1] - freqs2[p2])
                if distance < min_distance:
                    min_distance = distance
                    pair = (p1, p2)
        
        if pair is None: # No more pairs below the threshold
            break
        
        p1, p2 = pair
        paired_peaks.append(((p1, freqs1[p1], psd1[p1]), (p2, freqs2[p2], psd2[p2])))
        unpaired_peaks1.remove(p1)
        unpaired_peaks2.remove(p2)
    
    return paired_peaks, unpaired_peaks1, unpaired_peaks2


######################################################################
# Computation of a basic signal spectrogram
######################################################################

def calc_specgram(data):
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


######################################################################
# Computation of the differential spectrogram
######################################################################

# Performs a standard bilinear interpolation for a given x, y point based on surrounding input grid values. This function
# is part of the logic to re-align both belts spectrogram in order to combine them in the differential spectrogram.
def bilinear_interpolate(x, y, points, values):
    x1, x2 = points[0]
    y1, y2 = points[1]
    
    f11, f12 = values[0]
    f21, f22 = values[1]
    
    interpolated_value = (
        (f11 * (x2 - x) * (y2 - y) +
         f21 * (x - x1) * (y2 - y) +
         f12 * (x2 - x) * (y - y1) +
         f22 * (x - x1) * (y - y1)) / ((x2 - x1) * (y2 - y1))
    )

    return interpolated_value


# Interpolate source_data (2D) to match target_x and target_y in order to interpolate and
# get similar time and frequency dimensions for the differential spectrogram
def interpolate_2d(target_x, target_y, source_x, source_y, source_data):
    interpolated_data = np.zeros((len(target_y), len(target_x)))
    
    for i, y in enumerate(target_y):
        for j, x in enumerate(target_x):
            # Find indices of surrounding points in source data
            # and ensure we don't exceed array bounds
            x_indices = np.searchsorted(source_x, x) - 1
            y_indices = np.searchsorted(source_y, y) - 1
            x_indices = max(0, min(len(source_x) - 2, x_indices))
            y_indices = max(0, min(len(source_y) - 2, y_indices))
            
            x1, x2 = source_x[x_indices], source_x[x_indices + 1]
            y1, y2 = source_y[y_indices], source_y[y_indices + 1]
            
            f11 = source_data[y_indices, x_indices]
            f12 = source_data[y_indices, x_indices + 1]
            f21 = source_data[y_indices + 1, x_indices]
            f22 = source_data[y_indices + 1, x_indices + 1]
            
            interpolated_data[i, j] = bilinear_interpolate(x, y, ((x1, x2), (y1, y2)), ((f11, f12), (f21, f22)))

    return interpolated_data


# This function identifies a "ridge" of high gradient magnitude in a spectrogram (pdata) - ie. a resonance diagonal line. Starting from
# the maximum value in the first column, it iteratively follows the direction of the highest gradient in the vicinity (window configured using
# the n_average parameter). The result is a sequence of indices that traces the resonance line across the original spectrogram.
def detect_ridge(pdata, n_average=3):
    grad_y, grad_x = np.gradient(pdata)
    magnitude = np.sqrt(grad_x**2 + grad_y**2)
    
    # Start at the maximum value in the first column
    start_idx = np.argmax(pdata[:, 0])
    path = [start_idx]
    
    # Walk through the spectrogram following the path of the ridge
    for j in range(1, pdata.shape[1]):
        # Look in the vicinity of the previous point
        vicinity = magnitude[max(0, path[-1]-n_average):min(pdata.shape[0], path[-1]+n_average+1), j]
        # Take an average of top few points
        sorted_indices = np.argsort(vicinity)
        top_indices = sorted_indices[-n_average:]
        next_idx = int(np.mean(top_indices) + max(0, path[-1]-n_average))
        path.append(next_idx)
    
    return np.array(path)


# This function calculates the time offset between two resonances lines (ridge1 and ridge2) using cross-correlation in
# the frequency domain (using FFT). The result provides the lag (or offset) at which the two sequences are most similar.
# This is used to re-align both belts spectrograms on their resonances lines in order to create the combined spectrogram.
def compute_cross_correlation_offset(ridge1, ridge2):
    # Ensure that the two arrays have the same shape
    if len(ridge1) < len(ridge2):
        ridge1 = np.pad(ridge1, (0, len(ridge2) - len(ridge1)))
    elif len(ridge1) > len(ridge2):
        ridge2 = np.pad(ridge2, (0, len(ridge1) - len(ridge2)))

    cross_corr = np.fft.fftshift(np.fft.ifft(np.fft.fft(ridge1) * np.conj(np.fft.fft(ridge2))))
    return np.argmax(np.abs(cross_corr)) - len(ridge1) // 2


# This function shifts data along its second dimension - ie. time here - by a specified shift_amount
def shift_data_in_time(data, shift_amount):
    if shift_amount > 0:
        return np.pad(data, ((0, 0), (shift_amount, 0)), mode='constant')[:, :-shift_amount]
    elif shift_amount < 0:
        return np.pad(data, ((0, 0), (0, -shift_amount)), mode='constant')[:, -shift_amount:]
    else:
        return data


# Main logic function to combine two similar spectrogram - ie. from both belts paths - by detecting similarities (ridges), computing
# the time lag and realigning them. Finally this function combine (by substracting signals) the aligned spectrograms in a new one.
# This result of a mostly zero-ed new spectrogram with some colored zones highlighting differences in the belts paths.
def combined_spectrogram(data1, data2):
    pdata1, bins1, t1 = calc_specgram(data1)
    pdata2, _, _ = calc_specgram(data2)

    # Detect ridges
    ridge1 = detect_ridge(pdata1)
    ridge2 = detect_ridge(pdata2)

    # Compute offset using cross-correlation and shit/align and interpolate the spectrograms
    offset = compute_cross_correlation_offset(ridge1, ridge2)
    pdata2_aligned = shift_data_in_time(pdata2, offset)
    pdata2_interpolated = interpolate_2d(t1, bins1, t1, bins1, pdata2_aligned)

    # Combine the spectrograms
    combined_data = np.abs(pdata1 - pdata2_interpolated)
    return combined_data, bins1, t1


# Compute a composite and highly subjective value indicating the "chance of mechanical issues on the printer (0 to 100%)"
# that is based on the differential spectrogram sum of gradient salted with a bit of the estimated similarity cross-correlation
# from compute_curve_similarity_factor() and with a bit of the number of unpaired peaks.
# This result in a percentage value quantifying the machine behavior around the main resonances that give an hint if only touching belt tension
# will give good graphs or if there is a chance of mechanical issues in the background (above 50% should be considered as probably problematic)
def compute_comi(combined_data, similarity_coefficient, num_unpaired_peaks):
    filtered_data = combined_data[combined_data > 100]

    # First compute a "total variability metric" based on the sum of the gradient that sum the magnitude of will emphasize regions of the
    # spectrogram where there are rapid changes in magnitude (like the edges of resonance peaks).
    total_variability_metric = np.sum(np.abs(np.gradient(filtered_data)))
    # Scale the metric to a percentage using the threshold (found empirically on a large number of user data shared to me)
    base_percentage = (np.log1p(total_variability_metric) / np.log1p(DC_THRESHOLD_METRIC)) * 100
    
    # Adjust the percentage based on the similarity_coefficient to add a grain of salt
    adjusted_percentage = base_percentage * (1 - DC_GRAIN_OF_SALT_FACTOR * (similarity_coefficient / 100))

    # Adjust the percentage again based on the number of unpaired peaks to add a second grain of salt
    peak_confidence = num_unpaired_peaks / DC_MAX_UNPAIRED_PEAKS_ALLOWED
    final_percentage = (1 - peak_confidence) * adjusted_percentage + peak_confidence * 100
    
    # Ensure the result lies between 0 and 100 by clipping the computed value
    final_percentage = np.clip(final_percentage, 0, 100)
    
    return final_percentage


######################################################################
# Graphing
######################################################################

def plot_compare_frequency(ax, lognames, signal1, signal2, max_freq):
    # Plot the two belts PSD signals
    ax.plot(signal1.freqs, signal1.psd, label="\n".join(wrap(lognames[0], 60)), alpha=0.6)
    ax.plot(signal2.freqs, signal2.psd, label="\n".join(wrap(lognames[1], 60)), alpha=0.6)

    # Trace the "relax region" (also used as a threshold to filter and detect the peaks)
    psd_lowest_max = min(signal1.psd.max(), signal2.psd.max())
    peaks_warning_threshold = PEAKS_DETECTION_THRESHOLD * psd_lowest_max
    ax.axhline(y=peaks_warning_threshold, color='black', linestyle='--', linewidth=0.5)
    ax.fill_between(signal1.freqs, 0, peaks_warning_threshold, color='green', alpha=0.15, label='Relax Region')

    # Trace and annotate the peaks on the graph
    paired_peak_count = 0
    unpaired_peak_count = 0
    offsets_table_data = []

    for _, (peak1, peak2) in enumerate(signal1.paired_peaks):
        label = ALPHABET[paired_peak_count]
        amplitude_offset = abs(((signal2.psd[peak2[0]] - signal1.psd[peak1[0]]) / max(signal1.psd[peak1[0]], signal2.psd[peak2[0]])) * 100)
        frequency_offset = abs(signal2.freqs[peak2[0]] - signal1.freqs[peak1[0]])
        offsets_table_data.append([f"Peaks {label}", f"{frequency_offset:.2f} Hz", f"{amplitude_offset:.2f} %"])
        
        ax.plot(signal1.freqs[peak1[0]], signal1.psd[peak1[0]], "x", color='black')
        ax.plot(signal2.freqs[peak2[0]], signal2.psd[peak2[0]], "x", color='black')
        ax.plot([signal1.freqs[peak1[0]], signal2.freqs[peak2[0]]], [signal1.psd[peak1[0]], signal2.psd[peak2[0]]], ":", color='gray')
        
        ax.annotate(label + "1", (signal1.freqs[peak1[0]], signal1.psd[peak1[0]]),
                    textcoords="offset points", xytext=(8, 5),
                    ha='left', fontsize=14, color='black')
        ax.annotate(label + "2", (signal2.freqs[peak2[0]], signal2.psd[peak2[0]]),
                    textcoords="offset points", xytext=(8, 5),
                    ha='left', fontsize=14, color='black')
        paired_peak_count += 1

    for peak in signal1.unpaired_peaks:
        ax.plot(signal1.freqs[peak], signal1.psd[peak], "x", color='black')
        ax.annotate(str(unpaired_peak_count + 1), (signal1.freqs[peak], signal1.psd[peak]),
                    textcoords="offset points", xytext=(8, 5),
                    ha='left', fontsize=14, color='red', weight='bold')
        unpaired_peak_count += 1

    for peak in signal2.unpaired_peaks:
        ax.plot(signal2.freqs[peak], signal2.psd[peak], "x", color='black')
        ax.annotate(str(unpaired_peak_count + 1), (signal2.freqs[peak], signal2.psd[peak]),
                    textcoords="offset points", xytext=(8, 5),
                    ha='left', fontsize=14, color='red', weight='bold')
        unpaired_peak_count += 1

    # Compute the similarity (using cross-correlation of the PSD signals)
    similarity_factor = compute_curve_similarity_factor(signal1, signal2)
    ax.plot([], [], ' ', label=f'Estimated similarity: {similarity_factor:.1f}% ({unpaired_peak_count} unpaired peaks)')
    print(f"Belts estimated similarity: {similarity_factor:.1f}%")

    # Setting axis parameters, grid and graph title
    ax.set_xlabel('Frequency (Hz)')
    ax.set_xlim([0, max_freq])
    ax.set_ylabel('Power spectral density')
    psd_highest_max = max(signal1.psd.max(), signal2.psd.max())
    ax.set_ylim([0, psd_highest_max + psd_highest_max * 0.05])

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
    ax.grid(which='major', color='grey')
    ax.grid(which='minor', color='lightgrey')
    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('small')
    ax.set_title('Belts Frequency Profiles (estimated similarity: {:.1f}%)'.format(similarity_factor), fontsize=14)
    ax.legend(loc='best', prop=fontP)

    # Print the table of offsets ontop of the graph below the original legend (upper right)
    if len(offsets_table_data) > 0:
        columns = ["", "Frequency delta", "Amplitude delta", ]
        offset_table = ax.table(cellText=offsets_table_data, colLabels=columns, bbox=[0.67, 0.60, 0.3, 0.2], loc='upper right', cellLoc='center')
        offset_table.auto_set_font_size(False)
        offset_table.set_fontsize(8)
        offset_table.auto_set_column_width([0, 1, 2])
        offset_table.set_zorder(100)
        cells = [key for key in offset_table.get_celld().keys()]
        for cell in cells:
            offset_table[cell].set_facecolor('white')
            offset_table[cell].set_alpha(0.6)

    return similarity_factor, unpaired_peak_count


def plot_difference_spectrogram(ax, data1, data2, signal1, signal2, similarity_factor, max_freq):
    combined_data, bins, t = combined_spectrogram(data1, data2)

    # Compute the COMI value from the differential spectrogram sum of gradient, salted with
    # the similarity factor and the number or unpaired peaks from the belts frequency profile
    # Be careful, this value is highly opinionated and is pretty experimental!
    comi = compute_comi(combined_data, similarity_factor, len(signal1.unpaired_peaks) + len(signal2.unpaired_peaks))
    print(f"Chances of mechanical issues: {comi:.1f}%")
    ax.set_title(f"Differential Spectrogram (COMI: {comi:.1f}%)", fontsize=14)
    ax.plot([], [], ' ', label=f'Chances of mechanical issues (COMI): {comi:.1f}%')
    
    # Draw the differential spectrogram with a specific norm to get light grey zero values and red for max values (vmin to vcenter is not used)
    norm = matplotlib.colors.TwoSlopeNorm(vcenter=np.min(combined_data), vmax=np.max(combined_data))
    ax.pcolormesh(bins, t, combined_data.T, cmap='RdBu_r', norm=norm, shading='gouraud')
    ax.set_xlabel('Frequency (hz)')
    ax.set_xlim([0., max_freq])
    ax.set_ylabel('Time (s)')
    ax.set_ylim([0, t[-1]])

    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('medium')
    ax.legend(loc='best', prop=fontP)

    # Plot vertical lines for unpaired peaks
    unpaired_peak_count = 0
    for _, peak in enumerate(signal1.unpaired_peaks):
        ax.axvline(signal1.freqs[peak], color='red', linestyle='dotted', linewidth=1.5)
        ax.annotate(f"Peak {unpaired_peak_count + 1}", (signal1.freqs[peak], t[-1]*0.05),
                    textcoords="data", color='red', rotation=90, fontsize=10,
                    verticalalignment='bottom', horizontalalignment='right')
        unpaired_peak_count +=1

    for _, peak in enumerate(signal2.unpaired_peaks):
        ax.axvline(signal2.freqs[peak], color='red', linestyle='dotted', linewidth=1.5)
        ax.annotate(f"Peak {unpaired_peak_count + 1}", (signal2.freqs[peak], t[-1]*0.05),
                    textcoords="data", color='red', rotation=90, fontsize=10,
                    verticalalignment='bottom', horizontalalignment='right')
        unpaired_peak_count +=1
    
    # Plot vertical lines and zones for paired peaks
    for idx, (peak1, peak2) in enumerate(signal1.paired_peaks):
        label = ALPHABET[idx]
        x_min = min(peak1[1], peak2[1])
        x_max = max(peak1[1], peak2[1])
        ax.axvline(x_min, color='blue', linestyle='dotted', linewidth=1.5)
        ax.axvline(x_max, color='blue', linestyle='dotted', linewidth=1.5)
        ax.fill_between([x_min, x_max], 0, np.max(combined_data), color='blue', alpha=0.3)
        ax.annotate(f"Peaks {label}", (x_min, t[-1]*0.05),
                textcoords="data", color='blue', rotation=90, fontsize=10,
                verticalalignment='bottom', horizontalalignment='right')

    return


######################################################################
# Custom tools 
######################################################################

# Simple helper to compute a sigmoid scalling (from 0 to 100%)
def sigmoid_scale(x, k=1):
    return 1 / (1 + np.exp(-k * x)) * 100

# Original Klipper function to get the PSD data of a raw accelerometer signal
def compute_signal_data(data, max_freq):
    calibration_data = calc_freq_response(data)
    freqs = calibration_data.freq_bins[calibration_data.freq_bins <= max_freq]
    psd = calibration_data.get_psd('all')[calibration_data.freq_bins <= max_freq]
    peaks, _ = detect_peaks(psd, freqs)
    return SignalData(freqs=freqs, psd=psd, peaks=peaks, paired_peaks=None, unpaired_peaks=None)
 

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
               "graph_accelerometer.py script to process it instead." % (logname,))


def setup_klipper_import(kdir):
    global shaper_calibrate
    kdir = os.path.expanduser(kdir)
    sys.path.append(os.path.join(kdir, 'klippy'))
    shaper_calibrate = importlib.import_module('.shaper_calibrate', 'extras')


def belts_calibration(lognames, klipperdir="~/klipper", max_freq=200.):
    setup_klipper_import(klipperdir)

    # Parse data
    datas = [parse_log(fn) for fn in lognames]
    if len(datas) > 2:
        raise ValueError("Incorrect number of .csv files used (this function needs two files to compare them)")

    # Compute calibration data for the two datasets with automatic peaks detection
    signal1 = compute_signal_data(datas[0], max_freq)
    signal2 = compute_signal_data(datas[1], max_freq)

    # Pair the peaks across the two datasets
    paired_peaks, unpaired_peaks1, unpaired_peaks2 = pair_peaks(signal1.peaks, signal1.freqs, signal1.psd,
                                                               signal2.peaks, signal2.freqs, signal2.psd)
    signal1 = signal1._replace(paired_peaks=paired_peaks, unpaired_peaks=unpaired_peaks1)
    signal2 = signal2._replace(paired_peaks=paired_peaks, unpaired_peaks=unpaired_peaks2)

    fig = matplotlib.pyplot.figure()
    gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[4, 3])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    fig.suptitle("CoreXY relative belt calibration tool", fontsize=16)

    similarity_factor, _ = plot_compare_frequency(ax1, lognames, signal1, signal2, max_freq)
    plot_difference_spectrogram(ax2, datas[0], datas[1], signal1, signal2, similarity_factor, max_freq)

    fig.set_size_inches(10, 12)
    fig.tight_layout()
    fig.subplots_adjust(top=0.93)
    
    return fig


def main():
    # Parse command-line arguments
    usage = "%prog [options] <raw logs>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-o", "--output", type="string", dest="output",
                    default=None, help="filename of output graph")
    opts.add_option("-f", "--max_freq", type="float", default=200.,
                    help="maximum frequency to graph")
    opts.add_option("-k", "--klipper_dir", type="string", dest="klipperdir",
                    default="~/klipper", help="main klipper directory")
    options, args = opts.parse_args()
    if len(args) < 1:
        opts.error("Incorrect number of arguments")
    if options.output is None:
        opts.error("You must specify an output file.png to use the script (option -o)")

    fig = belts_calibration(args, options.klipperdir, options.max_freq)
    fig.savefig(options.output)


if __name__ == '__main__':
    main()
