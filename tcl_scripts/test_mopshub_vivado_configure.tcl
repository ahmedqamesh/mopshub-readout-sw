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
set project_name "mopshub_board_v2TMR"
set vivado_project_path     "/home/dcs/git/mopshub/Vivado/${project_name}"
set expectedProjectPath     "$vivado_project_path/$project_name/$project_name.xpr"
set ila_probe_file 	    "$vivado_project_path/$project_name/$project_name.runs/impl_1/${project_name}_wrapper.ltx"
set bitstream_file 	    "$vivado_project_path/$project_name/$project_name.runs/impl_1/${project_name}_wrapper.bit"
set bitstream_golden_file   "$vivado_project_path/$project_name/$project_name.runs/${project_name}_wrapper_golden.bit"
set bitstream_feedback_file "$vivado_project_path/$project_name/$project_name.runs/${project_name}_wrapper_feedback.bit"
set vivado_ip_out_path      "$root_dir/output_dir/${time_now}_vivado_configure/"
set out_logFile 	    [file join $vivado_ip_out_path "${time_now}_log_file.txt"]

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
    if {$level ne "DATA"} {
	puts $::logFileId $level:$message
    }
}

# Define a procedure to create a directory if it doesn't exist
proc create_directory_if_not_exists {dir_path} {
    if {![file exists $dir_path]} {
	file mkdir $dir_path
    }
}

# Define a procedure to program the target device
proc program_target_device {bitstream_file_in} {
    specialPrint "INFO" "Programming target device with the $bitstream_file_in"
    # Set the properties for the target device
    set_property PROBES.FILE $::ila_probe_file [get_hw_devices xc7a200t_0]
    set_property FULL_PROBES.FILE $::ila_probe_file [get_hw_devices xc7a200t_0]
    set_property PROGRAM.FILE $bitstream_file_in [get_hw_devices xc7a200t_0]
    program_hw_devices [get_hw_devices xc7a200t_0]
    refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
    #display_hw_ila_data [ get_hw_ila_data hw_ila_data_1 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_board_v2_i/ila_0"}]]
    #display_hw_ila_data [ get_hw_ila_data hw_ila_data_2 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_board_v2_i/ila_1"}]]
    refresh_hw_device [lindex [get_hw_devices xc7a35t_0] 0]
	
}

#Define a procedure to program  the configuration memory
proc program_configuration_memory {} {
    set mcs_file_path [file join $::vivado_project_path "sdk" "${::project_name}_boot.mcs"]
    set prm_file_path [file join $::vivado_project_path "sdk" "${::project_name}_boot.prm"]
    specialPrint "REPORT" "MCS file: $mcs_file_path"
    specialPrint "REPORT" "PRM file: $prm_file_path"
    specialPrint "INFO" "Set the configuration memory: is25lp128f-spi-x1_x2_x4"
    create_hw_cfgmem -hw_device [lindex [get_hw_devices xc7a200t_0] 0] [lindex [get_cfgmem_parts {is25lp128f-spi-x1_x2_x4}] 0]
    set_property PROGRAM.BLANK_CHECK  0 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.ERASE  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.CFG_PROGRAM  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.VERIFY  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.CHECKSUM  0 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
	
    specialPrint "INFO" "Programming the configuration memory using $mcs_file_path"	
    set_property PROGRAM.ADDRESS_RANGE  {use_file} [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]    
    set_property PROGRAM.FILES [list $mcs_file_path] [get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.PRM_FILE {$prm_file_path} [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.UNUSED_PIN_TERMINATION {pull-none} [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
	
    set_property PROGRAM.BLANK_CHECK  0 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.ERASE  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.CFG_PROGRAM  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.VERIFY  1 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    set_property PROGRAM.CHECKSUM  0 [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    startgroup 
    create_hw_bitstream -hw_device [lindex [get_hw_devices xc7a200t_0] 0] [get_property PROGRAM.HW_CFGMEM_BITFILE [ lindex [get_hw_devices xc7a200t_0] 0]]; program_hw_devices [lindex [get_hw_devices xc7a200t_0] 0]; refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0];
    program_hw_cfgmem -hw_cfgmem [ get_property PROGRAM.HW_CFGMEM [lindex [get_hw_devices xc7a200t_0] 0]]
    endgroup	
    refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
}
create_directory_if_not_exist $vivado_ip_out_path
set logFileId [open $::out_logFile "w"]
specialPrint "INFO" "Starting Time $::time_now"
specialPrint "INFO" "Creating test files at $::vivado_ip_out_path"

#=======================Open the device=======================================================================
#disconnect_hw_server
open_hw_manager
connect_hw_server -allow_non_jtag
#update_compile_order -fileset sources_1

set hw_targets [get_hw_targets]
set target_device [lindex $hw_targets 0]
open_hw_target [lindex $target_device 0]
specialPrint "INFO" "Opening the Target Device$target_device" 
#set target_device "localhost:3121/xilinx_tcf/Digilent/210299B38601"
#open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299B38601}
refresh_hw_device [get_hw_devices xc7a200t_0]

# Set the JTAG frequency
#set_property PARAM.FREQUENCY 15000000 [get_hw_targets $target_device]
set jtag_freq [get_property PARAM.FREQUENCY [get_hw_targets $target_device]]
specialPrint "REPORT"  "JTAG Frequecy:$jtag_freq Hz"
#=======================Bitstream data=======================================================================
specialPrint "INFO" "Preparing Bitstream files"
specialPrint "REPORT" "Access $::bitstream_golden_file"
program_target_device $bitstream_golden_file

# Get the size of the bitstream file
set size_of_first_bitstream_bytes [file size $bitstream_golden_file]
set programming_time [expr {$size_of_first_bitstream_bytes / ($jtag_freq / 8)}]
# Start address of the bitstreams
set start_address_of_first_bitstream 0x000000
set start_address_of_second_bitstream_hex 0x0049FD5E
set start_address_of_third_bitstream_hex 0x0093FABC

# Extract Memory information
# Size of a sector in bytes
set sector_size_bytes [expr {4 * 1024}]  ;# 4 KB
# Calculate the number of sectors each bitstream occupies
set sectors_per_bitstream [expr {$size_of_first_bitstream_bytes / $sector_size_bytes}]
# Calculate the start and end addresses for the sectors occupied by the bitstream
set start_address_of_first_bitstream_sector $start_address_of_first_bitstream
set end_address_of_first_bitstream_sector [expr {$size_of_first_bitstream_bytes + ($sectors_per_bitstream) * $sector_size_bytes}]

specialPrint "REPORT"  "Bitstream file size: $size_of_first_bitstream_bytes bytes"
specialPrint "REPORT"  "Estimated programming time: $programming_time seconds"
# Display the start address of the bitstreams
specialPrint "REPORT" "Sectors per bitstream: $sectors_per_bitstream"
specialPrint "REPORT" "start_address_of_second_bitstream_hex =  $start_address_of_second_bitstream_hex"
specialPrint "REPORT" "start_address_of_third_bitstream_hex =  $start_address_of_third_bitstream_hex"
#=======================configure Memory=======================================================================
# Build the command string
specialPrint "INFO" "Configuring the configuration memory"
set write_cfgmem_command "write_cfgmem  -format mcs -size 16 -interface SPIx4 -loadbit {up $start_address_of_first_bitstream \"$bitstream_golden_file\" up $start_address_of_second_bitstream_hex \"$bitstream_feedback_file\" up $start_address_of_third_bitstream_hex \"$bitstream_feedback_file\"} -checksum -force -file \"$vivado_project_path/sdk/${project_name}_boot.mcs\""
# Execute the command
eval $write_cfgmem_command

program_configuration_memory
specialPrint "INFO" "Boot HW device"
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
boot_hw_device  [lindex [get_hw_devices xc7a200t_0] 0]
specialPrint "REPORT" "Wait for 3 seconds" 
after 3000
specialPrint "INFO" "Refresh and Initialize HW" 
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
disconnect_hw_server
connect_hw_server -allow_non_jtag 
set hw_targets [get_hw_targets]
set target_device [lindex $hw_targets 0]
open_hw_target [lindex $target_device 0]
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
#readback_hw_cfgmem -hw_cfgmem [get_property PROGRAM.HW_CFGMEM [get_hw_devices xc7a200t_0 ]] -file $vivado_project_path/mopshub_design_16bus_readback.mcs -format MCS -force -all
disconnect_hw_server
set time_end [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
set time_elapsed "[expr {([clock clicks -millisec]-$time_start)/1000.}] sec" ;# RS
specialPrint "INFO" "End Time $time_end"
specialPrint "INFO" "Time elapsed $time_elapsed"
specialPrint "SUCCESS" "CLOSE $::out_logFile"
close $logFileId
