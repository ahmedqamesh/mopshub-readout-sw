# 1) Open a TCL Shell using vivado -mode tcl
# 2) source this script
#vivado -mode batch -source tcl
# Get the current time in the desired format
set time_now [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
set time_start [clock clicks -millisec]
# Get the full path of the currently running script
set script_path [file normalize [info script]]
# Extract the directory path from the script path
set root_dir [file dirname $script_path]
# Set the root directory as the current working directory
cd $root_dir
set project_name "mopshub_board_v3TMR"
set vivado_project_path     "/home/dcs/git/mopshub/vivado/mopshub_v3TMR"
set bitstream_file 	    "$vivado_project_path/$project_name/$project_name.runs/impl_1/${project_name}_wrapper.bit"
set ila_probe_file 	    "$vivado_project_path/$project_name/$project_name.runs/impl_1/${project_name}_wrapper.ltx"
set bitstream_golden_file   "$vivado_project_path/$project_name/$project_name.runs/${project_name}_wrapper_golden.bit"
set bitstream_fallback_file "$vivado_project_path/$project_name/$project_name.runs/${project_name}_wrapper_fallback.bit"

set vivado_ip_out_path  $root_dir/output_dir/${time_now}_vivado_configure/

# Define a procedure for printing information with special formatting
proc specialPrint {level message} {
    # Define ANSI color escape sequences
    set colorReset "\033\[0m"
    switch $level {
	   #red color
	"ERROR " { 
	    set colorCode "\033\[31m"
	}
	    #green color
	"INFO" {
	    set colorCode "\033\[32m"
	}
	    #Bold yellow color with White Background
	"WARNING" {
	    set colorCode "\033\[1m\033\[33m\033\[47m"
	}
	#bold green
	"SUCCESS" {
		set colorCode "\033\[1m\033\[32m"
	    }	    
	    #blue color
	"REPORT" {
	    set colorCode "\033\[34m"
	}
	    #cyan color
	    "NOTICE" {
		set colorCode "\033\[36m"
	    }
	    #blue color
	    "DATA" {
		set colorCode "\033\[1m"
	    }	    
	default {
	    set colorCode "\033\[0m" ;# Default to no color
	}
    }
    puts "${colorCode}$level:$colorReset ${colorCode}$message $colorReset"
}

#=======================Bitstream data=======================================================================
specialPrint "INFO" "Preparing Bitstream files"
specialPrint "REPORT" "Access $::bitstream_golden_file"

# Get the size of the bitstream file
set size_of_golden_bitstream_bytes [file size $bitstream_golden_file ]
set size_of_golden_bitstream_Mbytes [expr {$size_of_golden_bitstream_bytes/1000000}]
set size_of_feedback_bitstream_bytes [file size $bitstream_golden_file]
# Start address of the bitstreams
set start_address_of_first_bitstream 0x000000
set end_address_of_first_bitstream [expr {$start_address_of_first_bitstream + $size_of_golden_bitstream_bytes}]

set start_address_of_second_bitstream_hex [format "0x00%X" $end_address_of_first_bitstream]
set end_address_of_second_bitstream [expr {$start_address_of_second_bitstream_hex + $size_of_feedback_bitstream_bytes}]

set start_address_of_third_bitstream_hex [format "0x00%X" $end_address_of_second_bitstream]
set end_address_of_third_bitstream [expr {$start_address_of_third_bitstream_hex + $size_of_feedback_bitstream_bytes}]

set start_address_of_forth_bitstream_hex [format "0x00%X" $end_address_of_third_bitstream]
set end_address_of_forth_bitstream [expr {$start_address_of_forth_bitstream_hex + $size_of_feedback_bitstream_bytes}]

set start_address_of_fifth_bitstream_hex [format "0x00%X" $end_address_of_forth_bitstream]
set end_address_of_fifth_bitstream [expr {$start_address_of_fifth_bitstream_hex + $size_of_feedback_bitstream_bytes}]


# Extract Memory information
# Size of a sector in bytes
set sector_size_bytes [expr {4 * 1024}]  ;# 4 KB
# Calculate the number of sectors each bitstream occupies
set sectors_per_bitstream [expr {$size_of_golden_bitstream_bytes / $sector_size_bytes}]
# Calculate the start and end addresses for the sectors occupied by the bitstream
set start_address_of_first_bitstream_sector $start_address_of_first_bitstream
set end_address_of_first_bitstream_sector [expr {$size_of_golden_bitstream_bytes + ($sectors_per_bitstream) * $sector_size_bytes}]


specialPrint "REPORT"  "Bitstream file size: $size_of_golden_bitstream_Mbytes  Mbytes"

# Display the start address of the bitstreams
specialPrint "REPORT" "Sectors per bitstream: $sectors_per_bitstream"
#specialPrint "REPORT" "First Bitstream sectors =$sectors_per_bitstream : $start_address_of_first_bitstream_sector & $end_address_of_first_bitstream_sector"
specialPrint "REPORT" "start_address_of_second_bitstream_hex =  $start_address_of_second_bitstream_hex"
specialPrint "REPORT" "start_address_of_third_bitstream_hex =  $start_address_of_third_bitstream_hex"
specialPrint "REPORT" "start_address_of_forth_bitstream_hex =  $start_address_of_forth_bitstream_hex"
specialPrint "SUCCESS" "Closing the script"	
