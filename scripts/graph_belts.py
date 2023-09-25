#!/usr/bin/env python3

#################################################
######## CoreXY BELTS CALIBRATION SCRIPT ########
#################################################
# Written by Frix_x#0161 #
# @version: 1.0

# CHANGELOG:
#   v1.0: first version of this tool


# Be sure to make this script executable using SSH: type 'chmod +x ./graph_belts.py' when in the folder!

#####################################################################
################ !!! DO NOT EDIT BELOW THIS LINE !!! ################
#####################################################################

import optparse, matplotlib, sys, importlib, os
from textwrap import wrap
import numpy as np
import matplotlib.pyplot, matplotlib.dates, matplotlib.font_manager
import matplotlib.ticker, matplotlib.gridspec, matplotlib.colors

matplotlib.use('Agg')

MAX_TITLE_LENGTH=65
PEAKS_DETECTION_THRESHOLD=0.20


######################################################################
# Computation of the PSD graph
######################################################################

# Calculate estimated "power spectral density"
def calc_freq_response(data):
    helper = shaper_calibrate.ShaperCalibrate(printer=None)
    return helper.process_accelerometer_data(data)


def compute_curve_similarity_factor(data1, data2, max_freq):
    # Calculate the frequency response (FFT) for both datasets
    calibration_data1 = calc_freq_response(data1)
    calibration_data2 = calc_freq_response(data2)
    
    # Extract the frequency bins and PSDs up to max_freq
    freqs1 = calibration_data1.freq_bins[calibration_data1.freq_bins <= max_freq]
    psd1 = calibration_data1.get_psd('all')[calibration_data1.freq_bins <= max_freq]
    
    freqs2 = calibration_data2.freq_bins[calibration_data2.freq_bins <= max_freq]
    psd2 = calibration_data2.get_psd('all')[calibration_data2.freq_bins <= max_freq]
    
    # Interpolate PSDs to match the same frequency bins
    psd2_interp = np.interp(freqs1, freqs2, psd2)

    # Compute cross-correlation
    cross_corr = np.correlate(psd1, psd2_interp, mode='full')
    
    # Find the peak of the cross-correlation
    peak_value = np.max(cross_corr)
    
    # Compute similarity measure (normalized by the energy in the signals)
    similarity = peak_value / (np.sqrt(np.sum(psd1**2) * np.sum(psd2_interp**2)))

    # Apply sigmoid scaling
    k = 1.5  # adjust this as needed
    scaled_similarity = 1 / (1 + np.exp(-(-np.log(1 - similarity) / k))) * 100
    
    return scaled_similarity


def detect_peaks(psd):
    peaks = np.where((psd[:-2] < psd[1:-1]) & (psd[1:-1] > psd[2:]))[0] + 1
    detection_threshold  = PEAKS_DETECTION_THRESHOLD * psd.max()

    peaks = peaks[psd[peaks] > detection_threshold]
    num_peaks = len(peaks)

    return peaks, num_peaks


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

# Bilinear interpolation for a point (x, y) based on values from surrounding points to handle
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
# get similar time and frequency dimensions for the comparison spectrogram
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


def compute_cross_correlation_offset(ridge1, ridge2):
    # Ensure that the two arrays have the same shape
    if len(ridge1) < len(ridge2):
        ridge1 = np.pad(ridge1, (0, len(ridge2) - len(ridge1)))
    elif len(ridge1) > len(ridge2):
        ridge2 = np.pad(ridge2, (0, len(ridge1) - len(ridge2)))

    cross_corr = np.fft.fftshift(np.fft.ifft(np.fft.fft(ridge1) * np.conj(np.fft.fft(ridge2))))
    return np.argmax(np.abs(cross_corr)) - len(ridge1) // 2


def shift_data_in_time(data, shift_amount):
    if shift_amount > 0:
        return np.pad(data, ((0, 0), (shift_amount, 0)), mode='constant')[:, :-shift_amount]
    elif shift_amount < 0:
        return np.pad(data, ((0, 0), (0, -shift_amount)), mode='constant')[:, -shift_amount:]
    else:
        return data


def combine_spectrograms(data1, data2):
    pdata1, bins1, t1 = calc_specgram(data1)
    pdata2, _, _ = calc_specgram(data2)

    # Detect ridges
    ridge1 = detect_ridge(pdata1)
    ridge2 = detect_ridge(pdata2)

    # Compute offset using cross-correlation
    offset = compute_cross_correlation_offset(ridge1, ridge2)

    # Shift the second spectrogram to align it with the first
    pdata2_aligned = shift_data_in_time(pdata2, offset)
    
    # Ensure both spectrograms are on the same grid
    pdata2_interpolated = interpolate_2d(t1, bins1, t1, bins1, pdata2_aligned)

    # Combine the spectrograms
    combined_data = np.where(np.abs(pdata1) > np.abs(pdata2_interpolated), pdata1, -pdata2_interpolated)

    return -combined_data, bins1, t1


def compute_imbalance_difference_factor(combined_data, threshold_factor=0.05):
    threshold = threshold_factor * np.max(np.abs(combined_data))
    
    # Total energy
    total_energy = np.sum(np.abs(combined_data))
    
    # Imbalance energy
    imbalance_energy = np.sum(np.abs(combined_data[np.abs(combined_data) > threshold]))
    
    # Compute the difference factor
    difference_factor = (imbalance_energy / (total_energy + 1e-7)) * 100
    
    return difference_factor


######################################################################
# Graphing
######################################################################

def plot_compare_frequency(ax, datas, lognames, max_freq):
    ax.set_xlabel('Frequency (Hz)')
    ax.set_ylabel('Power spectral density')

    for data, logname in zip(datas, lognames):
        calibration_data = calc_freq_response(data)
        freqs = calibration_data.freq_bins
        psd = calibration_data.get_psd('all')[freqs <= max_freq]
        freqs = freqs[freqs <= max_freq]
        ax.plot(freqs, psd, label="\n".join(wrap(logname, 60)), alpha=0.6)

        peaks, _ = detect_peaks(psd)
        ax.plot(freqs[peaks], psd[peaks], "x", color='black', markersize=8)
        for idx, peak in enumerate(peaks):
            if psd[peak] > 1:
                fontcolor = 'red'
                fontweight = 'bold'
            else:
                fontcolor = 'black'
                fontweight = 'normal'
            ax.annotate(f"{idx+1}", (freqs[peak], psd[peak]), 
                        textcoords="offset points", xytext=(8, 5), 
                        ha='left', fontsize=14, color=fontcolor, weight=fontweight)
    
    similarity_factor = compute_curve_similarity_factor(datas[0], datas[1], max_freq)
    ax.plot([], [], ' ', label='Estimated similarity: {:.1f}%'.format(similarity_factor))

    ax.xaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.yaxis.set_minor_locator(matplotlib.ticker.AutoMinorLocator())
    ax.ticklabel_format(axis='y', style='scientific', scilimits=(0,0))
    ax.grid(which='major', color='grey')
    ax.grid(which='minor', color='lightgrey')
    fontP = matplotlib.font_manager.FontProperties()
    fontP.set_size('x-small')
    ax.set_title('Belts Frequency Profiles (estimated similarity: {:.1f}%)'.format(similarity_factor))
    ax.legend(loc='best', prop=fontP)

    return


# Plot data in a "spectrogram colormap"
def plot_specgram(ax, data, logname, max_freq):
    pdata, bins, t = calc_specgram(data)

    ax.set_title("\n".join(wrap("Spectrogram (%s)" % (logname),
                 MAX_TITLE_LENGTH)))
    ax.pcolormesh(bins, t, pdata.T, norm=matplotlib.colors.LogNorm(), cmap='inferno', shading='gouraud')
    ax.set_xlim([0., max_freq])
    ax.set_xlabel('Frequency (hz)')
    ax.set_ylabel('Time (s)')
    
    return


def plot_difference_specgram(ax, data1, data2, lognames, max_freq):
    combined_data, bins, t = combine_spectrograms(data1, data2)

    # Set the midpoint of the colormap to be centered around 0
    norm = matplotlib.colors.TwoSlopeNorm(vmin=np.min(combined_data), vmax=np.max(combined_data), vcenter=0)

    ax.set_title("Difference Spectrogram")
    ax.pcolormesh(bins, t, combined_data.T, cmap='coolwarm', norm=norm, shading='gouraud')
    ax.set_xlim([0., max_freq])
    ax.set_xlabel('Frequency (hz)')
    ax.set_ylabel('Time (s)')

    # Compute and display the difference factor on the graph
    diff_factor = compute_imbalance_difference_factor(combined_data)
    ax.text(0.05, 0.95, 'Belt Imbalance Percentage: {:.2f}%'.format(diff_factor),
            transform=ax.transAxes, fontsize=10, va='top', ha='left', bbox=dict(facecolor='white', alpha=0.7))

    return


######################################################################
# Startup and main routines
######################################################################

def parse_log(logname, opts):
    with open(logname) as f:
        for header in f:
            if not header.startswith('#'):
                break
        if not header.startswith('freq,psd_x,psd_y,psd_z,psd_xyz'):
            # Raw accelerometer data
            return np.loadtxt(logname, comments='#', delimiter=',')
    # Power spectral density data or shaper calibration data
    opts.error("File %s does not contain raw accelerometer data and therefore "
               "is not supported by this script. Please use the official Klipper"
               "graph_accelerometer.py script to process it instead." % (logname,))


def setup_klipper_import(kdir):
    global shaper_calibrate
    sys.path.append(os.path.join(kdir, 'klippy'))
    shaper_calibrate = importlib.import_module('.shaper_calibrate', 'extras')


def main():
    # Parse command-line arguments
    usage = "%prog [options] <raw logs>"
    opts = optparse.OptionParser(usage)
    opts.add_option("-o", "--output", type="string", dest="output",
                    default=None, help="filename of output graph")
    opts.add_option("-f", "--max_freq", type="float", default=200.,
                    help="maximum frequency to graph")
    opts.add_option("-k", "--klipper_dir", type="string", dest="klipperdir",
                    default="/home/pi/klipper", help="main klipper directory")
    options, args = opts.parse_args()
    if len(args) < 1:
        opts.error("Incorrect number of arguments")

    setup_klipper_import(options.klipperdir)

    # Parse data
    datas = [parse_log(fn, opts) for fn in args]

    fig = matplotlib.pyplot.figure()
    gs = matplotlib.gridspec.GridSpec(2, 1, height_ratios=[4, 3])
    ax1 = fig.add_subplot(gs[0])
    ax2 = fig.add_subplot(gs[1])
    fig.suptitle("CoreXY belts calibration tool", fontsize=16)
    
    plot_compare_frequency(ax1, datas, args, options.max_freq)
    plot_difference_specgram(ax2, datas[0], datas[1], args, options.max_freq)

    if options.output is None:
        matplotlib.pyplot.show()
    else:
        fig.set_size_inches(10, 12)
        fig.tight_layout()
        fig.subplots_adjust(top=0.93)
        fig.savefig(options.output)


if __name__ == '__main__':
    main()
