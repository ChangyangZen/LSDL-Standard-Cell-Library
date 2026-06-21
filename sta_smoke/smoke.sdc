# smoke.sdc — SDC for the 1-cell LSDL STA spike.
#
# Two interleaved clocks C1 and C2, both 50% duty, 180-deg phase
# (matches paper Fig. 2a L1/L2 pipeline). For this 1-cell smoke we
# only use C1.
#
# Period 2 ns -> 500 MHz target (well below the LSDL eval-delay limit
# at slow corner so STA should report positive slack).

set period 2.0
set hperiod [expr {$period / 2.0}]

create_clock -name C1 -period $period -waveform "0 $hperiod" [get_ports c1]

# Input arrival: data driven at the start of the cycle by an upstream
# C2-domain cell. C2 is half a cycle out of phase from C1, so data
# arrives 1.0 ns before each C1 rising edge.
set_input_delay  -clock C1 -max [expr {$period * 0.5 - 0.2}] [get_ports data_in]
set_input_delay  -clock C1 -min 0.10 [get_ports data_in]   ;# > cell hold (0.05ns)

# Output: assume downstream C2-domain cell needs 0.2 ns of slack.
set_output_delay -clock C1 -max 0.2 [get_ports data_out]
set_output_delay -clock C1 -min 0.0 [get_ports data_out]

# Load on the output.
set_load 10.0 [get_ports data_out]
