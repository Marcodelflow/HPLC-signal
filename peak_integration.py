import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from scipy.signal import find_peaks
from scipy.integrate import trapezoid


def read_chromatogram(file_path, channel):
    """This function opens a csv file that contains the chromatogram data and
    return the data as numpy arrays.

    Input:
      filename: path of the correpsonding csv file
      channel:
    Output:
      x: array of time (or number of data)
      y: intensity of signal"""

    # Reading .csv file with chromatogram data
    print("\tOpening file")
    df = pd.read_csv(file_path, sep=";", decimal=".")

    # dataFrame to one-dimensiolnal numpuy array
    y = df[channel].to_numpy()
    y = np.reshape(y, y.size)

    # Finite difference calculation
    print("\tComputing first derivative\n")
    # First derivative
    dy = np.convolve(y, [1, -1]) / 1
    # Second derivative (for future analysis)
    ddy = np.convolve(dy[1:], [1, -1]) / 1

    # Define new formatted DataFrame
    df_out = pd.DataFrame({channel: y, "First diff": dy[1:], "Second diff": ddy[1:]})

    return df_out


def plot_derivatives(
    data,
    xlim,
    same_plot="True",
):
    """This function plots your chromatogram, the first derivative, and the
    second derivative"""

    # plt.axvline(x=interval[0], color="r", linestyle="--")
    # plt.axvline(x=interval[1], color="r", linestyle="--")

    colors = ["tab:blue", "tab:orange", "tab:green"]
    # Plot columns in data
    if same_plot == "True":
        fig, axes = plt.subplots(figsize=(10, 5))
        plt.xlim(xlim)

        for i, key in enumerate(data.keys()):
            data[key].plot(label=key, color=colors[i])

        plt.grid()
        plt.legend()

    elif same_plot == "False":
        fig, axes = plt.subplots(3, figsize=(15, 10), sharex=True)
        plt.xlim(xlim)
        plt.grid()

        for i, key in enumerate(data.keys()):
            data[key].plot(
                ax=axes[i], grid="True", ylabel="Intensity", label=key, color=colors[i]
            )
            axes[i].legend()

        plt.legend()

    plt.show()


def peak_finder(data, intervals, image="None"):
    """This function finds peaks in your chromatogram, the arrangen and
    filter the data in te intervals This function assume the same atributes
    for all the chromamtograms

    Input:

    Output:"""

    # PEAK FIND USING SCIPY
    # The configuration can be change here.

    print("Peak identification".center(50, "="))
    # Peak identification with scipy function
    peaks, prop = find_peaks(
        data.iloc[:, 0].to_numpy(),
        height=4000,  # [min,max]
        threshold=1,  # Threshold is basically the noise level
        distance=2,  # Horizontal distance >=1
        prominence=None,
        width=None,
        wlen=None,
        rel_height=0.5,
        plateau_size=None,
    )

    # Dataframe with information of all peaks in the chromatogram
    pre_peak_data = pd.DataFrame({"index": peaks, "height": prop["peak_heights"]})
    print("Peak information:\n", pre_peak_data)

    # Filter peaks in intervals and store them in dictionary
    post_peak_data = {}
    for i, interval in enumerate(intervals):
        post_peak_data[str(interval)] = pre_peak_data[
            (pre_peak_data.iloc[:, 0] > interval[0])
            & (pre_peak_data.iloc[:, 0] < interval[1])
        ]

    # Print the dictionary to check results
    for key in post_peak_data:
        print("\nin range: ", key)
        print(post_peak_data[key])

    # Plot peaks in user intervals (OPTIONAL)
    if image == "True":
        fig, ax = plt.subplots(figsize=(10, 5))
        data.iloc[:, 0].plot(grid="True", ylabel="Intensity", label="chromatogram")

        # Get y limits
        _, ymax = ax.get_ylim()

        for i, interval in enumerate(intervals):
            # Plot intervals
            plt.axvline(x=interval[0], color="tab:orange", linestyle="dotted")
            plt.axvline(x=interval[1], color="tab:orange", linestyle="dotted")
            # Add text to intervals
            plt.text(
                interval[0],
                ymax * 0.5,
                "user interval " + str(i + 1),
                ha="center",
                va="center",
                rotation="vertical",
                backgroundcolor="white",
            )
            # Plot peaks in intervals
            peak_info = post_peak_data[str(interval)]
            x = peak_info.iloc[:, 0]
            y = peak_info.iloc[:, 1]
            plt.scatter(x, y, s=20, marker="x", color="red")

        plt.show()

    return post_peak_data


def limits_finder(chroma_data, peaks_data, intervals, min_slope=1, image="None"):
    """This function find the limits of specified peaks as indexes.

    Inputs
       peaks_data: dictionary that contains peaks information (index,height)
       stored in different keys (intervals as string)
    Output
       out_peaks_data: dictionary that contains peaks information (index,height,
       limits_idx, limits_val)
       stored in different keys (intervals as string)"""

    print("Limits find".center(50, "="))
    # x[a],x[b] are the limits of peak integration.
    y = chroma_data.iloc[:, 0].to_numpy()
    dy = chroma_data.iloc[:, 1].to_numpy()
    dy = np.absolute(dy)
    print(dy)

    out_peak_data = {}
    # Intervals loop for multiple intervals
    for key in peaks_data:
        print("\nProcessing peaks in :", key)
        peaks_info = peaks_data[key]  # extract peak info from interval

        limits_val = []  # Preallocation
        limits_idx = []  # Preallocation

        # Peaks loop for multiple peaks in interval
        for i in range(0, len(peaks_info)):
            peak_idx = peaks_info.iloc[:, 0].to_numpy()  # extract peak indexes
            # print(peak_idx[i])

            limit_val = ["None"] * 2
            limit_idx = ["None"] * 2

            # will it be necessary to add another noise reduction method? for
            # example moving avarange, or this one
            # https://stackoverflow.com/questions/37598986/reducing-noise-on-data

            # width  move de index in order to avoid selectin de same peak
            # as limits, because the first derivative is almost zero at the peak
            width = 5

            # Forward slope finding
            for j in range(peak_idx[i] + width, len(dy)):
                print("index: ", j, "slope: ", dy[j])
                if abs(dy[j]) < min_slope:
                    limit_idx[1] = j
                    limit_val[1] = y[j]
                    break

            # Backward slope finding
            for j in reversed(range(0, peak_idx[i] - width)):
                if abs(dy[j]) < min_slope:
                    limit_idx[0] = j
                    limit_val[0] = y[j]
                    break

            limits_idx.insert(i, limit_idx)  # Allocating integration limits
            limits_val.insert(i, limit_val)  # Allocating values

        peaks_info["limits idx"] = limits_idx  # Allocation all the limits
        peaks_info["limits val"] = limits_val

        print(peaks_info)

        peaks_data[key] = peaks_info

    # Plot peaks in user intervals (OPTIONAL)
    if image == "True":
        print("Plotting results".center(50, "="))
        fig, ax = plt.subplots(figsize=(10, 5))
        chroma_data.iloc[:, 0].plot(
            grid="True", ylabel="Intensity", label="chromatogram"
        )
        ax.plot(dy)

        # Get y limits
        _, ymax = ax.get_ylim()

        for i, interval in enumerate(intervals):
            # Plot intervals
            interval = list(interval)
            plt.axvline(x=interval[0], color="tab:orange", linestyle="dotted")
            plt.axvline(x=interval[1], color="tab:orange", linestyle="dotted")
            # Add text to intervals
            plt.text(
                interval[0],
                ymax * 0.5,
                "user interval " + str(i + 1),
                ha="center",
                va="center",
                rotation="vertical",
                backgroundcolor="white",
            )

            # Plot peaks in intervals
            peaks_info = peaks_data[str(interval)]
            print("ESTA ES LA INFO:\n", peaks_info)
            x_peak = peaks_info.iloc[:, 0]
            y_peak = peaks_info.iloc[:, 1]
            plt.scatter(x_peak, y_peak, s=20, marker="x", color="red")

            # Plot integration limits

            list_of_limits_idx = peaks_info.iloc[:, 2].to_numpy()
            list_of_limits_val = peaks_info.iloc[:, 3].to_numpy()
            print(list_of_limits_idx)
            for i in range(0, len(list_of_limits_idx)):
                x_ab = list_of_limits_idx[i]
                y_ab = list_of_limits_val[i]
                plt.scatter(x_ab, y_ab, s=20, marker="x", color="green")

        plt.show()

    return peaks_data


file_path = r"C:\Users\marco\Escritorio\chroma_plot\test_data\corrected_chromatograms\Data\A0_01.csv"
channel = "215nm"
# Time interval where to search the peak (INPUT)
intervals = [[100, 600], [1000, 1500], [2360, 2966]]

# Read chromatogram and computes the first and secon dderivatives
chroma_data = read_chromatogram(file_path, channel)
print(chroma_data)

# plot_derivatives(chroma_data, same_plot="True", xlim=[0, 3000])

# Find peaks in specified intervals
peaks_data = peak_finder(chroma_data, intervals, image="None")

peaks_data = limits_finder(
    chroma_data, peaks_data, intervals, min_slope=5, image="True"
)


# PEAK INTEGRATION
# areas = []
# limits = peaks_data["limits idx"].to_list()
# for i, peak in enumerate(peaks_data):
#  limit = limits[i]
# integration_data = peaks_data[
#     (peaks_data["index"] > limit[0]) & (peaks_data["index"] < limit[1])
# ]
# area = trapezoid(integration_data["Intensity"], integration_data["index"])
# areas.insert(i, area)

# print("Area are:", areas)
