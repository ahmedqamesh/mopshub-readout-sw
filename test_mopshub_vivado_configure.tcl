# Get the current time in the desired format
set time_now [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
set time_start [clock clicks -millisec]
set vivado_project_path "/run/media/dcs/data2/workspaces/mopshub_board"
set project_name "$vivado_project_path/mopshub_board.xpr"
set bitstream_golden_file $vivado_project_path/mopshub_board.runs/mopshub_design_16bus_new_wrapper_golden.bit
set bitstream_feedback_file $vivado_project_path/mopshub_board.runs/mopshub_design_16bus_new_wrapper_feedback.bit

# Get the full path of the currently running script
set script_path [file normalize [info script]]
# Extract the directory path from the script path
set root_dir [file dirname $script_path]
# Set the root directory as the current working directory
cd $root_dir

set target_device "localhost:3121/xilinx_tcf/Digilent/210299A568F6"

# Define a procedure for printing information with special formatting
proc specialPrint {name message color} {
    # Define ANSI color escape sequences
    set colorReset "\033\[0m"
    switch $color {
	"red" {
	    set colorCode "\033\[31m"
	}
	"green" {
	    set colorCode "\033\[32m"
	}
	"yellow" {
	    set colorCode "\033\[33m"
	}
	"blue" {
	    set colorCode "\033\[34m"
	}
	default {
	    set colorCode "\033\[0m" ;# Default to no color
	}
    }
    
    puts "\n**************************************"
    puts "*             $name           *"
    puts "**************************************\n"
    puts ">> $message"
    puts "\n**************************************\n"
}

# Define a procedure to create a directory if it doesn't exist
proc create_directory_if_not_exists {dir_path} {
    if {![file exists $dir_path]} {
	file mkdir $dir_path
    }
}

# Define a procedure to program the target device
proc program_target_device {bitstream_golden_file} {
    specialPrint "Program" "Programming target device" "green"
    # Set the paths to the bitstream file and ILA probe file
    global vivado_project_path
    global ila_probe_file
    
    # Set the properties for the target device
    set_property PROBES.FILE $ila_probe_file [get_hw_devices xc7a200t_0]
    set_property FULL_PROBES.FILE $ila_probe_file [get_hw_devices xc7a200t_0]
    set_property PROGRAM.FILE $bitstream_golden_file [get_hw_devices xc7a200t_0]
    program_hw_devices [get_hw_devices xc7a200t_0]
    refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
    display_hw_ila_data [ get_hw_ila_data hw_ila_data_1_16 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]]
    display_hw_ila_data [ get_hw_ila_data hw_ila_data_2 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_1"}]]
    refresh_hw_device [lindex [get_hw_devices xc7a35t_0] 0]
	
}

#Define a procedure to program  the configuration memory
proc program_configuration_memory {} {
    specialPrint "Program" "Programming  the configuration memory" "green"
    # Set the paths to the bitstream file and ILA probe file
    global vivado_project_path
    set mcs_file_path [file join $vivado_project_path "mopshub_board.sdk" "mopshub_board_boot.mcs"]
    set prm_file_path [file join $vivado_project_path "mopshub_board.sdk" "mopshub_board_boot.prm"]
    create_hw_cfgmem -hw_device [lindex [get_hw_devices xc7a200t_0] 0] [lindex [get_cfgmem_parts {is25lp128f-spi-x1_x2_x4}] 0]
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
}


#=======================Open the device=======================================================================
#open_project $project_name
specialPrint "Status" "Opening the Target Device$target_device" "yellow"
update_compile_order -fileset sources_1
disconnect_hw_server
connect_hw_server -allow_non_jtag 
open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299A568F6}
refresh_hw_device [get_hw_devices xc7a200t_0]
#=======================Bitstream data=======================================================================
specialPrint "Status" "Preparing Bitstream files" "yellow"
#program_target_device $bitstream_golden_file
# Set the JTAG frequency
#set_property PARAM.FREQUENCY 15000000 [get_hw_targets $target_device]
set jtag_freq [get_property PARAM.FREQUENCY [get_hw_targets $target_device]]
puts "JTAG Frequecy:$jtag_freq Hz"

# Get the size of the bitstream file
set size_of_first_bitstream_bytes [file size $bitstream_golden_file]
set programming_time [expr {$size_of_first_bitstream_bytes / ($jtag_freq / 8)}]
# Start address of the bitstreams
set start_address_of_first_bitstream 0x000000
set end_address_of_first_bitstream [expr {$start_address_of_first_bitstream + $size_of_first_bitstream_bytes}]
set start_address_of_second_bitstream_hex [format "0x00%X" $end_address_of_first_bitstream]
set end_address_of_second_bitstream [expr {$start_address_of_second_bitstream_hex + $size_of_first_bitstream_bytes}]
set start_address_of_third_bitstream_hex [format "0x00%X" $end_address_of_second_bitstream]
# Extract Memory information
# Size of a sector in bytes
set sector_size_bytes [expr {4 * 1024}]  ;# 4 KB
# Calculate the number of sectors each bitstream occupies
set sectors_per_bitstream [expr {$size_of_first_bitstream_bytes / $sector_size_bytes}]
# Calculate the start and end addresses for the sectors occupied by the bitstream
set start_address_of_first_bitstream_sector $start_address_of_first_bitstream
set end_address_of_first_bitstream_sector [expr {$size_of_first_bitstream_bytes + ($sectors_per_bitstream) * $sector_size_bytes}]

# Print the information
# Print the full XADC output path
puts "Full XADC output file: $full_xadc_out_file"
puts "Bitstream file size: $size_of_first_bitstream_bytes bytes"
puts "Estimated programming time: $programming_time seconds"

# Display the start address of the bitstreams
puts "Sectors per bitstream: $sectors_per_bitstream"
puts "First Bitstream sectors =$sectors_per_bitstream : $start_address_of_first_bitstream_sector & $end_address_of_first_bitstream_sector"
puts "start_address_of_second_bitstream_hex =  $start_address_of_second_bitstream_hex"

#=======================configure Memory=======================================================================
# Build the command string
specialPrint "Configure" "Configuring the configuration memory" "green"
set write_cfgmem_command "write_cfgmem  -format mcs -size 16 -interface SPIx4 -loadbit {up $start_address_of_first_bitstream \"$bitstream_golden_file\" up $start_address_of_second_bitstream_hex \"$bitstream_feedback_file\" up $start_address_of_third_bitstream_hex \"$bitstream_feedback_file\"} -checksum -force -file \"$vivado_project_path/mopshub_board.sdk/mopshub_board_boot.mcs\""
# Execute the command
eval $write_cfgmem_command
program_configuration_memory
specialPrint "Update" "Boot HW device" "blue"
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
boot_hw_device  [lindex [get_hw_devices xc7a200t_0] 0]
# Wait for 3 seconds
specialPrint "Status" "Wait for 3 seconds" "yellow"
after 3000
specialPrint "Status" "Refresh and Initialize HW" "yellow"
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
disconnect_hw_server
connect_hw_server -allow_non_jtag 
open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299A568F6}
refresh_hw_device [lindex [get_hw_devices xc7a200t_0] 0]
display_hw_ila_data [ get_hw_ila_data hw_ila_data_1 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]]
display_hw_ila_data [ get_hw_ila_data hw_ila_data_2 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_1"}]]
refresh_hw_device [lindex [get_hw_devices xc7a35t_0] 0]

#readback_hw_cfgmem -hw_cfgmem [get_property PROGRAM.HW_CFGMEM [get_hw_devices xc7a200t_0 ]] -file $vivado_project_path/mopshub_design_16bus_readback.mcs -format MCS -force -all
set time_elapsed "[expr {([clock clicks -millisec]-$time_start)/1000.}] sec" ;# RS
specialPrint "END" "Time elabsed $time_elapsed" "green"


