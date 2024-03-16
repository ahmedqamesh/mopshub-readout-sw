# Get the current time in the desired format
set time_now [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
set time_start [clock clicks -millisec]
set vivado_project_path "/run/media/dcs/data2/workspaces/mopshub_board"
set project_name "$vivado_project_path/mopshub_board.xpr"
set ila_data "$vivado_project_path/mopshub_board.hw/backup/hw_ila_data_1.ila"
set ila_probe_file $vivado_project_path/mopshub_board.runs/impl_1/mopshub_design_16bus_new_wrapper.ltx

# Get the full path of the currently running script
set script_path [file normalize [info script]]
# Extract the directory path from the script path
set root_dir [file dirname $script_path]
# Set the root directory as the current working directory
cd $root_dir

set ila_out_file "${time_now}_ila_data_file.csv"
set xadc_out_file "${time_now}_hw_xadc_data_file.csv"

set vivado_ip_out_path  $root_dir/output_dir/${time_now}_vivado/

set full_xadc_out_file  [file join $vivado_ip_out_path $xadc_out_file]  
set full_ila_out_file  [file join $vivado_ip_out_path $ila_out_file]  
# Declare full_path as a global variable
global full_ila_out_file
global full_xadc_out_file
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

# Define a procedure to configure the ILA core
proc configure_ila_core {} {
    # Define the ILA core instance name
    specialPrint "configure" "Starting ILA Core" "green"
    set ila_instance hw_ila_1
    set probe_name status_heartbeat	
    run_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]
    wait_on_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]
    display_hw_ila_data [upload_hw_ila_data [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]]
    add_wave -into {hw_ila_data_1.wcfg} -radix hex { {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_classification} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_correction} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_essential} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_heartbeat} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_initialization} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_injection} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_observation} {mopshub_design_16bus_new_i/sem_controller_wrapp_0_status_uncorrectable} }
    run_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]
}


# Define a procedure to create a directory if it doesn't exist
proc create_directory_if_not_exists {dir_path} {
    if {![file exists $dir_path]} {
	file mkdir $dir_path
    }
}

proc read_xadc {end_time} {
	#open the file in append mode ("a").
	specialPrint "Status" "Read XADC data" "green"
	puts "Opened file: $::full_xadc_out_file"
	set fileId [open $::full_xadc_out_file "a"]
	puts "File ID:$fileId"
	set end 0
	while {$end < $end_time} {
		#the number 1000 indicates the loop will be run every second (1000 ms).
		#If you need a higher or lower frequency, adjust it.
		after 1000
		refresh_hw_sysmon [get_hw_sysmons]
		set systemTime [clock seconds]
		puts -nonewline $fileId [clock format $systemTime -format %H:%M:%S]
		puts -nonewline $fileId ","
		#this is the XADC properties that you want to have printed.
		#Add as many as you need.
		set temperature [get_property TEMPERATURE [get_hw_sysmons]]
		puts -nonewline $fileId $temperature
		puts -nonewline $fileId ","
		set vccaux [get_property VCCAUX [get_hw_sysmons]]
		puts -nonewline $fileId $vccaux
		puts -nonewline $fileId ","
		set vccbram [get_property VCCBRAM [get_hw_sysmons]]
		puts -nonewline $fileId $vccbram
		puts -nonewline $fileId ","
		set vccint [get_property VCCINT [get_hw_sysmons]]
		puts $fileId $vccint
		puts " "
		puts "time: [clock format $systemTime -format %Y-%m-%d_%H:%M:%S] | TEMPERATURE : $temperature |VCCAUX: $vccaux |VCCBRAM: $vccbram | VCCINT: $vccint"
		flush stdout
		incr end
	}
	close $fileId
	puts "End of data collection."
	puts "Data written to file $::full_xadc_out_file"
}
proc read_ila {end_time} {
	#open the file in append mode ("a").	
	configure_ila_core
        specialPrint "Status" "Read ILA data" "green"
        #puts "Opened file: $::full_xadc_out_file"
        #set fileId [open $::full_ila_out_file "a"]
        #puts "File ID:$fileId"


	set end 0
	while {$end < $end_time} {
		#the number 1000 indicates the loop will be run every second (1000 ms).
		#If you need a higher or lower frequency, adjust it.
		after 1000
		run_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]
		wait_on_hw_ila [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]                          
		display_hw_ila_data [upload_hw_ila_data [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_design_16bus_new_i/ila_0"}]]
		display_hw_ila_data
		incr end
	}
	#close $fileId
	#puts "End of data collection."
	#puts "Data written to file $::full_xadc_out_file"
}

#=======================Open the device=======================================================================
open_hw_manager
specialPrint "Status" "Opening the Target Device$target_device" "yellow"
update_compile_order -fileset sources_1
disconnect_hw_server
connect_hw_server -allow_non_jtag 
open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299A568F6}
refresh_hw_device [get_hw_devices xc7a200t_0]

#=======================Read XADC data=======================================================================
create_directory_if_not_exist $vivado_ip_out_path

# Check if the file exists
if {![file exists $full_xadc_out_file]} {
    # If the file doesn't exist, write headers
    set fileId [open $::full_xadc_out_file "w"]
    puts -nonewline $fileId "Times"
    puts -nonewline $fileId ","
    puts -nonewline $fileId "TEMPERATURE"
    puts -nonewline $fileId ","
    puts -nonewline $fileId "VCCAUX"
    puts -nonewline $fileId ","
    puts -nonewline $fileId "VCCBRAM"
    puts -nonewline $fileId ","
    puts -nonewline $fileId "VCCINT"
    puts $fileId " "
    close $fileId
}
#read_xadc 5
#=======================Read ILA data=======================================================================
# Call the procedure to configure the ILA core
#get ila data name 
read_hw_ila_data $ila_data
#read_ila 5

# Write ila data into a file 
set ila_out_data [upload_hw_ila_data hw_ila_1]

if {[llength $ila_out_data] == 0} {
    puts "No ILA data available for export."
} else {
    # Write ILA data into a file
    write_hw_ila_data -csv_file -force $full_ila_out_file $ila_out_data
    puts "ILA data exported to $full_ila_out_file"
}
set time_elapsed "[expr {([clock clicks -millisec]-$time_start)/1000.}] sec" ;# RS

specialPrint "END" "Time elabsed $time_elapsed" "green"



