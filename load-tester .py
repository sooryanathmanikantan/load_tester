
import csv                     
import statistics            
import random               
from datetime import datetime  
import pyvisa                 



RAILS = [
    {"name": "+3V6", "voltage": 3.6, "tolerance": 0.05, "max_current": 2.5},
    {"name": "+1V8", "voltage": 1.8, "tolerance": 0.05, "max_current": 3.0},
    {"name": "+3V3", "voltage": 3.3, "tolerance": 0.05, "max_current": 3.0},
    {"name": "+2V5", "voltage": 2.5, "tolerance": 0.05, "max_current": 1.5},
]


MAX_DIP_FRACTION = 0.05
NUM_CAPTURES = 10

INSTRUMENT_ADDRESSES = {
    "power_supply":    "USB0::0x05E6::0x2230::INSTR",   # Keithley 2230-30-1
    "electronic_load": "USB0::0x05E6::0x2380::INSTR",   # Keithley 2380
    "oscilloscope":    "USB0::0x0957::0x1796::INSTR",   # Keysight DSOX6004A
}

def connect_instruments():
   
    try:
       
        rm = pyvisa.ResourceManager()
        instruments = {}
        for name, address in INSTRUMENT_ADDRESSES.items():
            inst = rm.open_resource(address)
            inst.timeout = 5000  
            instruments[name] = inst
        print("Connected to real instruments.")
        return instruments, False 
    except Exception as e:
      
        print(f"[SIMULATION MODE] No instruments found. Simulating readings.\n")
        return None, True         


def run_transient_test(rail, instruments, sim_mode):
    
    nominal = rail["voltage"]
    low_current = 0.1 * rail["max_current"]  
    high_current = 0.9 * rail["max_current"] 

    if not sim_mode:
      
        ps = instruments["power_supply"]
        load = instruments["electronic_load"]
        scope = instruments["oscilloscope"]

        ps.write(f"VOLT {nominal}")          
        ps.write("OUTP ON")                  
        load.write(f"CURR {low_current}")   
        load.write("INP ON")                

        scope.write("SINGLE")               
        load.write(f"CURR {high_current}")   

        v_min = float(scope.query("MEAS:VMIN? CHAN1"))
    else:
        
        dip = random.uniform(0.01, 0.06) * nominal
        v_min = nominal - dip

    return v_min

def run_all_tests_and_log(instruments, sim_mode, csv_filename):

    all_results = {} 

  
    with open(csv_filename, "w", newline="") as f:
        writer = csv.writer(f)
       
        writer.writerow(["Timestamp", "Rail", "Capture #", "Nominal (V)",
                         "Dip Min (V)", "Limit (V)", "Result"])

       
        for rail in RAILS:
            nominal = rail["voltage"]
            allowed_min = nominal * (1 - MAX_DIP_FRACTION)  
            dips = []  

            for capture in range(1, NUM_CAPTURES + 1):
                v_min = run_transient_test(rail, instruments, sim_mode)

                if v_min >= allowed_min:
                    result = "PASS"
                else:
                    result = "FAIL"

                timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

                writer.writerow([timestamp, rail["name"], capture,
                                 f"{nominal:.3f}", f"{v_min:.4f}",
                                 f"{allowed_min:.4f}", result])

                dips.append(v_min)  

            all_results[rail["name"]] = dips

    print(f"Results saved to {csv_filename}")
    return all_results


def calculate_statistics(all_results):
  
    stats_summary = {}

    for rail in RAILS:
        name = rail["name"]
        dips = all_results[name]
        allowed_min = rail["voltage"] * (1 - MAX_DIP_FRACTION)

        pass_count = 0
        for v in dips:
            if v >= allowed_min:
                pass_count += 1

        stats_summary[name] = {
            "mean":   statistics.mean(dips),    
            "min":    min(dips),               
            "max":    max(dips),                
            "stdev":  statistics.stdev(dips),   
            "passes": pass_count,              
            "total":  len(dips),                
        }

    return stats_summary

def generate_report(stats_summary, sim_mode, report_filename):
    
    lines = []
    lines.append("=" * 55)
    lines.append("   PDN LOAD TRANSIENT TEST REPORT")
    lines.append("=" * 55)
    lines.append(f"Date: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    lines.append(f"Mode: {'SIMULATION' if sim_mode else 'REAL INSTRUMENTS'}")
    lines.append(f"Captures per rail: {NUM_CAPTURES}")
    lines.append("-" * 55)

    overall_pass = True 

    for rail in RAILS:
        name = rail["name"]
        s = stats_summary[name]

        if s["passes"] == s["total"]:
            verdict = "PASS"
        else:
            verdict = "FAIL"
            overall_pass = False

        lines.append(f"Rail {name}:  [{verdict}]")
        lines.append(f"    Passed captures : {s['passes']}/{s['total']}")
        lines.append(f"    Worst-case dip  : {s['min']:.4f} V")
        lines.append(f"    Mean dip        : {s['mean']:.4f} V")
        lines.append(f"    Std deviation   : {s['stdev']:.4f} V")
        lines.append("-" * 55)

    lines.append(f"OVERALL RESULT: {'PASS' if overall_pass else 'FAIL'}")
    lines.append("=" * 55)

    report_text = "\n".join(lines)

    with open(report_filename, "w") as f:
        f.write(report_text)

    print(report_text)
    print(f"\nReport saved to {report_filename}")

def main():
    print("Starting PDN Load Transient Test...\n")
    instruments, sim_mode = connect_instruments()          # Step 2
    results = run_all_tests_and_log(instruments, sim_mode,
                                    "transient_results.csv")  # Steps 3 + 4
    stats = calculate_statistics(results)                  # Step 5
    generate_report(stats, sim_mode, "test_report.txt")    # Step 6

if __name__ == "__main__":
    main()