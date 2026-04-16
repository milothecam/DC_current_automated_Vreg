# DC_current_automated_Vreg

## What it does
These are the scripts for automating the DC current measurements using the Bluefors.

## How to run
This folder has three scripts of which only two matter:
- IV_measurement.py performs the measurements.
- IV_analysis.py is the rawest form of the analysis code. To use only this one would be ideal, in a scenario where we only measure useful data.
- IV_analysis_limitPts.py allows to use only part of all the data obtained using IV_measurement.py for analysis. The motivation for this is that data can be defective/useless.
  It also allows not to save the plots by default.

IV_measurement.py will manage lab equipment to apply a current (via a voltage source, for the moment...), measuring the current that is being drawn by the circuit, and recording an s2p file from a VNA measurement.
Files generated have a prefix (input) and will have a suffix which is the voltage that the source provided for such S-parameter measurement.
The script also looks at the temperature logs to plot the temperature variation of the channel that we are insterested on from the temperature monitor.

The analysis scripts will call the files using the names of the files (it will call the files by their names in the same way they were generated).
The analysis scripts will read the S-parameter values (magnitude and phase) at a given frequency (manual input).
They generate two plots: phase vs current(V), and phase normalization vs current(V). The normalization of the phase has to be reviewed but it is meant to estimate the I* of the devices of this study.

 
## Requirements
Lab equipment lol

## Example
Measure 61 S-parameter files with voltage steps between 0 and 0.35 V, with 61 seconds of pause between measurements:
```
Vdc_list = np.linspace(0, 0.35, 61).tolist()   # volts you want to apply (V_0, V_N, divs).
R_value = 1000.0                     # ohms (for final R vs I plot)
PAUSE_TIME = 61                      # seconds. Temp log happens every 60 sec.
TIMEOUT = 60000                      # ms
filePrefix = "InOut_Rs50ohm_0to035V_10mK"     # Prefix for files' names
```

Analysis has to match this calling of the data (voltages, steps, preffix, folder...)

## Notes
The plan is to get a current source and re arrange these scripts. Time (money) will tell.


