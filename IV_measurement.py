import time
import pathlib
import pyvisa
import matplotlib.pyplot as plt
import numpy as np
import csv

############################
# USER CONFIGURATION
############################
Vdc_list = np.linspace(0, 0.35, 61).tolist()   # volts you want to apply (V_0, V_N, divs).
R_value = 1000.0                     # ohms (for final R vs I plot)
PAUSE_TIME = 61                      # seconds. Temp log happens every 60 sec.
TIMEOUT = 60000                      # ms
filePrefix = "InOut_Rs50ohm_0to035V_10mK"     # Prefix for files' names

# Lakeshore log folder root
LAKESHORE_LOG_ROOT = pathlib.Path("C:/Users/bluefors/Documents/logging/temperature")

# Directory for output files
VNA_SAVE_DIR = pathlib.Path(r"C:\data\Camilo\Wafer UVA microstrip\microstrip E\DCcurrentAutomated\microstripE_Idc_10mK_3rdCD")
VNA_SAVE_DIR.mkdir(parents=True, exist_ok=True)

# Plot output directory (same folder as data)
PLOT_SAVE_DIR = VNA_SAVE_DIR
CHANNEL = 6

############################
# OPEN VISA INSTRUMENTS
############################
rm = pyvisa.ResourceManager()

PSU = rm.open_resource("USB0::0x2A8D::0x1002::MY61001323::0::INSTR")   # Keysight E36311A
DMM = rm.open_resource("USB0::0x2A8D::0x1301::MY60036848::0::INSTR")   # Keysight 34461A
VNA = rm.open_resource("TCPIP0::127.0.0.1::5025::SOCKET")              # Copper Mountain

VNA.read_termination = "\n"
VNA.timeout = TIMEOUT

print("PSU ID:", PSU.query("*IDN?").strip())
print("DMM ID:", DMM.query("*IDN?").strip())
print("VNA ID:", VNA.query("*IDN?").strip())

############################
# FUNCTIONS
############################

def read_lakeshore_temperature():
    """Reads last line of latest Lakeshore log folder. Returns temperature in mK."""
    latest_folder = sorted([x for x in LAKESHORE_LOG_ROOT.iterdir()])[-1]
    log_file = latest_folder / f"CH{CHANNEL} T {latest_folder.stem}.log"
    with log_file.open() as f:
        last = f.readlines()[-1]
        temp_K = float(last.split(",")[-1])
    return temp_K * 1e3  # convert to mK


def measure_sparams_s2p(full_path):
    """Saves an S2P Touchstone file from ports 3 & 4."""
    VNA.write("CALC:PAR:COUN 1")
    VNA.write("CALC:PAR1:DEF S34")
    VNA.write("CALC:PAR1:SEL")
    VNA.write("CALC:FORM MLOG")

    VNA.write("SENS:FREQ:CENT 10e9")
    VNA.write("SENS:FREQ:SPAN 20e9")
    VNA.write("SENS:SWE:POIN 10001")
    VNA.query("*OPC?")

    VNA.write("TRIG:SOUR BUS")
    VNA.write("TRIG:SING")
    VNA.query("*OPC?")

    VNA.write("MMEM:STOR:SNP:TYPE:S2P 3,4")
    VNA.write("MMEM:STOR:SNP:FORM DB")
    VNA.write(f'MMEM:STOR:SNP "{full_path.as_posix()}"')
    VNA.query("*OPC?")


def psu_set_voltage(volts):
    PSU.write("*RST")
    PSU.write("INST CH2")
    PSU.write(f"VOLT {volts}")
    PSU.write("CURR 1")
    PSU.write("OUTP ON")
    time.sleep(0.2)


def psu_off():
    PSU.write("OUTP OFF")


def measure_current():
    """Measure DC current using Keysight 34461A. Returns value in mA."""
    DMM.write("*RST")
    DMM.write("CONF:CURR:DC 1")     # 100 mA range
    reading = float(DMM.query("READ?"))
    return reading * 1000           # convert to mA


############################
# MAIN MEASUREMENT LOOP
############################

I_dc = []
T_list = []

for V in Vdc_list:
    print(f"\n=== Measuring at Vdc = {V} V ===")

    psu_set_voltage(V)

    s2p_filename = f"{filePrefix}_{V:.3f}V.s2p"
    full_path = VNA_SAVE_DIR / s2p_filename
    measure_sparams_s2p(full_path)
    print(f"Saved: {s2p_filename}")

    I = measure_current()
    I_dc.append(I)
    print(f"Measured current: {I:.6f} mA")

    T = read_lakeshore_temperature()
    T_list.append(T)
    print(f"Temperature: {T:.2f} mK")

    psu_off()
    time.sleep(PAUSE_TIME)


############################
# SAVE CSV
############################

print(f"Temperatures = {T_list} [mK]")
print(f"I_dc = {I_dc} [mA]")

csv_filename = VNA_SAVE_DIR / f"{filePrefix}_IVT.csv"
with csv_filename.open("w", newline="") as f:
    writer = csv.writer(f)
    writer.writerow(["Vdc_V", "Idc_mA", "Temperature_mK"])
    for V, I, T in zip(Vdc_list, I_dc, T_list):
        writer.writerow([V, I, T])

print(f"Saved CSV data to {csv_filename}")

############################
# PLOTTING
############################

# Figure 1: Current vs Voltage
fig1, ax1 = plt.subplots()
ax1.plot(Vdc_list, I_dc, marker='o')
ax1.set_xlabel("Vdc [V]")
ax1.set_ylabel("Idc [mA]")
ax1.set_title("Current vs Voltage")
ax1.grid(True)
fig1.tight_layout()
fig1_path = PLOT_SAVE_DIR / f"{filePrefix}_IV.png"
fig1.savefig(fig1_path, dpi=150)
print(f"Saved: {fig1_path.name}")

# Figure 2: Temperature vs Voltage
fig2, ax2 = plt.subplots()
ax2.plot(Vdc_list, T_list, marker='o')
ax2.set_xlabel("Vdc [V]")
ax2.set_ylabel("Temperature [mK]")
ax2.set_title("Temperature vs Voltage")
ax2.grid(True)
fig2.tight_layout()
fig2_path = PLOT_SAVE_DIR / f"{filePrefix}_TvsV.png"
fig2.savefig(fig2_path, dpi=150)
print(f"Saved: {fig2_path.name}")

plt.show()

############################
# CLEANUP
############################

print("Closing instrument connections...")
PSU.close()
DMM.close()
VNA.close()
rm.close()
print("Done.")
