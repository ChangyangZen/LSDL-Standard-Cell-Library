#!/usr/bin/env python3
"""gen_macro_views.py — emit the blackbox Verilog (.v) and a block-level
interface Liberty (.lib) for a pre-hardened macro, for integration into the
wafer.space gf180mcu-project-template (LibreLane Chip flow).

The block LEF + GDS come from our own OpenROAD/def2gds flow; this fills in the
two remaining macro views. The Liberty is an *interface* model: pins,
directions, capacitances, clock declarations, conservative output
max_capacitance — no internal arcs. The macro is internally clocked; its
boundary is constrained by SDC (input/output delay / false paths) at the top
level, exactly as a hard IP macro is handled. Upgrade to a full extracted
model later via OpenROAD write_timing_model if STA quality requires it.

Usage:
    python3 gen_macro_views.py <spec.json> <out_dir>
"""

import sys
import json
from pathlib import Path

INPUT_CAP = 0.005     # pf, conservative input pin cap
MAX_OUT_CAP = 0.5     # pf, conservative output drive limit


def bus_suffix(p):
    if 'msb' in p and 'lsb' in p:
        return f"[{p['msb']}:{p['lsb']}]"
    return ""


def each_bit(p):
    """Yield individual pin names for a (possibly bus) port."""
    if 'msb' in p and 'lsb' in p:
        hi, lo = p['msb'], p['lsb']
        step = 1 if hi >= lo else -1
        for i in range(lo, hi + step, step):
            yield f"{p['name']}[{i}]"
    else:
        yield p['name']


def gen_verilog(spec) -> str:
    """ANSI-style port declarations (matches the template's chip_top.sv): power
    pins live entirely inside `ifdef USE_POWER_PINS`, so the module compiles
    with or without the define. Yosys reads it power-aware (define set)."""
    design = spec['design']
    ports = spec['ports']
    pg = spec.get('power', {})
    pg_names = list(pg.keys())

    lines = [f"// {design} — blackbox view for the hardened macro.",
             "// Body intentionally empty: physical implementation is the",
             "// pre-hardened GDS/LEF; timing is the block .lib.",
             "`default_nettype none",
             "",
             f"module {design} ("]
    decls = []
    if pg_names:
        decls.append("    `ifdef USE_POWER_PINS")
        for pn in pg_names:
            decls.append(f"    inout  wire {pn},")
        decls.append("    `endif")
    for p in ports:
        b = bus_suffix(p)
        b = (b + " ") if b else ""
        decls.append(f"    {p['dir']:<6} wire {b}{p['name']},")
    # strip the trailing comma on the last real declaration
    for i in range(len(decls) - 1, -1, -1):
        if decls[i].strip().endswith(","):
            decls[i] = decls[i].rstrip().rstrip(",")
            break
    lines += decls
    lines += [");", "endmodule", "`default_nettype wire"]
    return "\n".join(lines) + "\n"


def pin_block(name, direction, is_clock, vdd, gnd) -> str:
    s = [f"    pin ({name}) {{", f"      direction : {direction} ;"]
    if vdd:
        s.append(f"      related_power_pin : {vdd} ;")
    if gnd:
        s.append(f"      related_ground_pin : {gnd} ;")
    if direction == "input":
        s.append(f"      capacitance : {INPUT_CAP} ;")
        if is_clock:
            s.append("      clock : true ;")
    else:
        s.append(f"      max_capacitance : {MAX_OUT_CAP} ;")
    s.append("    }")
    return "\n".join(s)


def gen_liberty(spec) -> str:
    design = spec['design']
    libname = f"{design}__tt_025C_5v00"
    clocks = set(spec.get('clocks', []))
    pg = spec.get('power', {})
    volt = spec.get('voltage', 5.0)
    vdd = next((p for p, k in pg.items() if k == "power"), None)
    gnd = next((p for p, k in pg.items() if k == "ground"), None)

    out = [f"library ({libname}) {{",
           "  technology (cmos);",
           "  delay_model : table_lookup;",
           "  time_unit : 1ns ;",
           "  voltage_unit : 1V ;",
           "  current_unit : 1mA ;",
           "  capacitive_load_unit (1, pf);",
           "  pulling_resistance_unit : 1ohm ;",
           "  leakage_power_unit : 1uW ;",
           "  slew_derate_from_library : 1.0 ;",
           "  slew_lower_threshold_pct_rise : 10.0 ;",
           "  slew_lower_threshold_pct_fall : 10.0 ;",
           "  slew_upper_threshold_pct_rise : 90.0 ;",
           "  slew_upper_threshold_pct_fall : 90.0 ;",
           "  input_threshold_pct_rise : 50.0 ;",
           "  input_threshold_pct_fall : 50.0 ;",
           "  output_threshold_pct_rise : 50.0 ;",
           "  output_threshold_pct_fall : 50.0 ;",
           "  nom_process : 1 ;",
           "  nom_temperature : 25 ;",
           f"  nom_voltage : {volt} ;"]
    for pn, kind in pg.items():
        out.append(f"  voltage_map({pn}, {volt if kind == 'power' else 0});")
    out += ["  default_max_transition : 1.5 ;",
            f"  operating_conditions (tt_025C_5v00) {{ process : 1 ; "
            f"temperature : 25 ; voltage : {volt} ; tree_type : balanced_tree ; }}",
            "  default_operating_conditions : tt_025C_5v00 ;",
            "",
            f"  cell ({design}) {{",
            "    is_macro_cell : true ;",
            "    dont_touch : true ;",
            "    dont_use : true ;"]
    for pn, kind in pg.items():
        pgtype = "primary_power" if kind == "power" else "primary_ground"
        out.append(f"    pg_pin ({pn}) {{ pg_type : {pgtype} ; "
                   f"voltage_name : {pn} ; }}")
    for p in spec['ports']:
        isclk = p['name'] in clocks
        for bit in each_bit(p):
            out.append(pin_block(bit, p['dir'], isclk, vdd, gnd))
    out += ["  }", "}"]
    return "\n".join(out) + "\n"


def main(spec_path, out_dir):
    spec = json.loads(Path(spec_path).read_text())
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    design = spec['design']
    (out / f"{design}.v").write_text(gen_verilog(spec))
    (out / f"{design}__tt_025C_5v00.lib").write_text(gen_liberty(spec))
    print(f"wrote {out / (design + '.v')}")
    print(f"wrote {out / (design + '__tt_025C_5v00.lib')}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
