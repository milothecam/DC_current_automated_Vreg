import math
import pathlib
import csv
import numpy as np
import matplotlib.pyplot as plt
import skrf as rf  # scikit-rf library for handling s2p files

############################
# USER CONFIGURATION
# Must match IV_measurement.py
############################

filePrefix  = "InOut_Rs50ohm_0to035V_10mK"
Vdc_list    = np.linspace(0, 0.35, 61).tolist()   # same linspace as measurement script

DATA_DIR    = pathlib.Path(r"C:\data\Camilo\Wafer UVA microstrip\microstrip E\DCcurrentAutomated\microstripE_Idc_10mK_3rdCD")
PLOT_SAVE_DIR = DATA_DIR / "plots"
PLOT_SAVE_DIR.mkdir(parents=True, exist_ok=True)

# S-parameter and frequency to analyse — still manual inputs
target_freq = 3.3e9    # Hz
sparam      = "s12"

############################
# LOAD CURRENTS FROM CSV
############################

csv_path = DATA_DIR / f"{filePrefix}_IVT.csv"

currents_mA = []
with csv_path.open("r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        # currents_mA.append(float(row["Idc_A"]))
        currents_mA.append(float(row["Idc_mA"]))

print(f"Loaded {len(currents_mA)} current values from {csv_path.name}")

############################
# BUILD FILENAMES FROM PREFIX + Vdc_list
############################

filenames = [str(DATA_DIR / f"{filePrefix}_{V:.3f}V.s2p") for V in Vdc_list]

# Sanity check: warn about any missing files
missing = [f for f in filenames if not pathlib.Path(f).exists()]
if missing:
    print(f"\nWARNING: {len(missing)} s2p file(s) not found:")
    for m in missing:
        print(f"  {m}")

# Keep only entries where both the file exists and a current value is available
n = min(len(filenames), len(currents_mA))
filenames   = filenames[:n]
currents_mA = currents_mA[:n]

valid = [(f, i) for f, i in zip(filenames, currents_mA) if pathlib.Path(f).exists()]
if not valid:
    raise FileNotFoundError("No valid s2p files found. Check DATA_DIR and filePrefix.")

filenames, currents_mA = zip(*valid)
filenames   = list(filenames)
currents_mA = list(currents_mA)

print(f"Analysing {len(filenames)} files at {target_freq/1e9:.3f} GHz  ({sparam.upper()})")

############################
# ANALYSIS FUNCTION
############################

def plot_s2p_phase_vs_current(filenames, currents, target_freq, sparam="s12",
                              xlabel="Applied Current [mA]",
                              ylabel="(Normalized Phase)^2",
                              ylabel_mag="|S-param| Magnitude [dB]",
                              title="(Normalized Phase)^2 vs Current with Constrained Quadratic Fit"):
    """
    Plot squared normalised phase of an S-parameter at a target frequency vs current,
    with a constrained quadratic fit (y = a*x^2 + 1).
    Magnitude on a secondary y-axis.
    Saves the figure automatically.
    """
    if len(filenames) != len(currents):
        raise ValueError("Number of filenames must match number of currents")

    phases        = []
    magnitudes_db = []

    for fname in filenames:
        ntwk  = rf.Network(fname)
        idx   = np.argmin(np.abs(ntwk.f - target_freq))
        i, j  = int(sparam[1]) - 1, int(sparam[2]) - 1
        s_val = ntwk.s[idx, i, j]
        phases.append(np.angle(s_val, deg=True))
        magnitudes_db.append(20 * np.log10(np.abs(s_val)))

    currents      = np.array(currents)
    phases        = np.array(phases)
    magnitudes_db = np.array(magnitudes_db)

    # Normalise phases by first value and square
    norm_phases = (phases / phases[0]) ** 2

    # Constrained quadratic fit: y = a*x^2 + 1
    X     = currents ** 2
    Y     = norm_phases - 1
    a_fit = np.dot(X, Y) / np.dot(X, X)

    x_fit = np.linspace(currents.min(), currents.max(), 200)
    y_fit = a_fit * x_fit ** 2 + 1

    aa  = math.sqrt(1 / abs(a_fit))
    eqn = f"y = {a_fit:.3e}·x² + 1  (I' = {aa:.3e} mA)"

    # ── Plot ──────────────────────────────────────────────────────────────────
    fig, ax1 = plt.subplots(figsize=(8, 6))

    ax1.scatter(currents, norm_phases, color="blue",
                label="(Phase/Phase[0])² data", zorder=3)
    ax1.plot(x_fit, y_fit, color="red", linestyle="--",
             label=f"Fit: {eqn}", zorder=2)
    ax1.set_xlabel(xlabel)
    ax1.set_ylabel(ylabel, color="blue")
    ax1.tick_params(axis="y", labelcolor="blue")
    ax1.grid(True, linestyle=":")

    ax2 = ax1.twinx()
    ax2.plot(currents, magnitudes_db, color="green", marker="s",
             linestyle="-", alpha=0.4, label=f"|{sparam.upper()}| [dB]")
    ax2.set_ylabel(ylabel_mag, color="green")
    ax2.tick_params(axis="y", labelcolor="green")

    handles1, labels1 = ax1.get_legend_handles_labels()
    handles2, labels2 = ax2.get_legend_handles_labels()
    ax1.legend(handles1 + handles2, labels1 + labels2, loc="best")

    plt.title(f"{title}\n({sparam.upper()} @ {target_freq/1e9:.3f} GHz)")
    fig.tight_layout()

    # Auto-save
    plot_name = f"{filePrefix}_{sparam.upper()}_{target_freq/1e9:.3f}GHz_phasefit.png"
    plot_path = PLOT_SAVE_DIR / plot_name
    fig.savefig(plot_path, dpi=150)
    print(f"Saved: {plot_path.name}")

    # ── Figure 2: Phase vs Current ────────────────────────────────────────────
    fig3, ax3 = plt.subplots(figsize=(7, 5))

    ax3.plot(currents, phases, color="purple", marker="o", linewidth=1.5,
             label=f"{sparam.upper()} phase")
    ax3.set_xlabel(xlabel)
    ax3.set_ylabel("Phase [deg]", color="purple")
    ax3.tick_params(axis="y", labelcolor="purple")
    ax3.grid(True, linestyle=":")
    ax3.legend(loc="best")

    plt.title(f"Phase vs Current\n({sparam.upper()} @ {target_freq/1e9:.3f} GHz)")
    fig3.tight_layout()

    plot_name3 = f"{filePrefix}_{sparam.upper()}_{target_freq/1e9:.3f}GHz_phase.png"
    plot_path3 = PLOT_SAVE_DIR / plot_name3
    fig3.savefig(plot_path3, dpi=150)
    print(f"Saved: {plot_path3.name}")

    plt.show()
    print(f"I' = {aa:.6f} mA")
    return currents, norm_phases, magnitudes_db, a_fit


############################
# RUN
############################

plot_s2p_phase_vs_current(filenames, currents_mA, target_freq, sparam=sparam)
