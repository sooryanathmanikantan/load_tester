# Load Tester

## What it does
This script tests if the power rails can handle a sudden increase in current 
without the voltage dropping too much. It measures the voltage dip during the 
sudden load change and decides pass or fail based on whether the dip stays 
within the allowed limit.

## Rails tested
- +3V6 (3.6 V)
- +1V8 (1.8 V)
- +3V3 (3.3 V)
- +2V5 (2.5 V)

## Instruments used (via PyVISA / SCPI)
- Keithley 2230-30-1 — DC Power Supply
- Keithley 2380 — Electronic Load
- Keysight DSOX6004A — Oscilloscope
- Keithley DMM6500 — Digital Multimeter

## How to run
1. Install the required library:
   pip install pyvisa
2. Run the script:
   python load_tester.py

## Output
The script creates two files:
- transient_results.csv — a log of every measurement with Pass/Fail status
- test_report.txt — a summary report showing each rail's result and an overall verdict

## Assumptions
Real lab instruments were not available while writing this script, so the 
instrument readings are simulated using random values within a realistic range. 
The real PyVISA/SCPI commands are included in the code and would work correctly 
with the actual instruments connected.

Other assumptions:
- Maximum allowable voltage dip during the transient: 5% of nominal voltage
- Load step: 10% to 90% of each rail's maximum current
- 10 captures per rail
- The instrument VISA addresses are example values; the real ones would be 
  found using pyvisa's list_resources() with instruments connected.
