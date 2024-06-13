# 1) Open a TCL Shell using vivado -mode tcl
# 2) source this script
set verbose off
# Get the current time in the desired format
set time_now [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
set time_start [clock clicks -millisec]
set project_name "mopshub_board_v3TMR"
set vivado_project_path "/home/dcs/git/mopshub/Vivado/$project_name"
set expectedProjectPath "$vivado_project_path/$project_name/$project_name.xpr"
set ila_data "$vivado_project_path/$project_name/$project_name.hw/backup/hw_ila_data_1.ila"
set ltx_file_path "$vivado_project_path/$project_name/$project_name.runs/impl_1/debug_nets.ltx"

# Get the full path of the currently running script
set script_path [file normalize [info script]]
# Extract the directory path from the script path
set root_dir [file dirname $script_path]
# Set the root directory as the current working directory
cd $root_dir
set vivado_ip_out_path  $root_dir/output_dir/${time_now}_vivado/

set full_xadc_out_file		[file join $vivado_ip_out_path "${time_now}_hw_xadc_file.csv"]
set full_ila_out_file_1  	[file join $vivado_ip_out_path "${time_now}_ila_data_file_1.csv"]
set out_logFile 		[file join $vivado_ip_out_path "${time_now}_log_file.txt"]
set full_ila_temp_file_1 [file join $vivado_ip_out_path "${time_now}_ila_temp_file_1.csv"]

# Declare full_path as a global variable
global full_xadc_out_file
global full_ila_out_file_1
global full_ila_temp_file_1
global ltx_file_path

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

proc checkForStopFlag {} {
    # Define the path to your flag file
    set flagFilePath "$::root_dir/kill_tcl"
    # Check if the flag file exists
    if {[file exists $flagFilePath]} {
	# If it exists, return 0 indicating the script should stop
	specialPrint "WARNING" "KILL reading process"
	return 0
    } else {
	# If it doesn't exist, return 1 indicating the script should continue
	return 1
    }
}

# Define a procedure to configure the ILA core
proc update_ila_cores {} {
    # Define the ILA core instance name
    specialPrint "INFO" "Starting ILA Cores"
    set hw_device [lindex [get_hw_devices] 0]
    set_property PROBES.FILE $::ltx_file_path $hw_device
    refresh_hw_device $::ltx_file_path
    # Select the ILA core
    set ila_core [get_hw_ilas hw_ila_1]

    # Arm the ILA core
    run_hw_ila $ila_core
    # Upload captured data from the ILA core
    upload_hw_ila_data $ila_core

    set ila_instance hw_ila_1
    set probe_name status_heartbeat
    run_hw_ila [get_hw_ilas -of_objects $hw_device -filter {CELL_NAME=~"mopshub_board_v2TMR_i/ila_0"}]
    wait_on_hw_ila [get_hw_ilas -of_objects $hw_device -filter {CELL_NAME=~"mopshub_board_v2TMR_i/ila_0"}]
    #display_hw_ila_data [upload_hw_ila_data [get_hw_ilas -of_objects $hw_device -filter {CELL_NAME=~"mopshub_board_v2TMR_i/ila_0"}]]
    display_hw_ila_data

}

proc read_xadc {end_time} {
    if {![file exists $::full_xadc_out_file]} {
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
    #open the file in append mode ("a").
    set fileId0 [open $::full_xadc_out_file "a"]
    specialPrint "INFO" "Read XADC data"
    specialPrint "REPORT" "OPEN $::full_xadc_out_file"
    set end 0
    # Check if the file exists
    while {[checkForStopFlag]} {
	#the number 1000 indicates the loop will be run every second (1000 ms).
	#If you need a higher or lower frequency, adjust it.
	after 1000
	refresh_hw_sysmon [get_hw_sysmons]
	set current_time [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
	puts -nonewline $fileId0 $current_time
	puts -nonewline $fileId0 ","
	#this is the XADC properties that you want to have printed.
	#Add as many as you need.
	set temperature [get_property TEMPERATURE [get_hw_sysmons]]
	puts -nonewline $fileId0 $temperature
	puts -nonewline $fileId0 ","
	set vccaux [get_property VCCAUX [get_hw_sysmons]]
	puts -nonewline $fileId0 $vccaux
	puts -nonewline $fileId0 ","
	set vccbram [get_property VCCBRAM [get_hw_sysmons]]
	puts -nonewline $fileId0 $vccbram
	puts -nonewline $fileId0 ","
	set vccint [get_property VCCINT [get_hw_sysmons]]
	puts $fileId0 $vccint
	specialPrint "DATA"  "time: $current_time | TEMPERATURE : $temperature |VCCAUX: $vccaux |VCCBRAM: $vccbram | VCCINT: $vccint"
	flush stdout
	incr end
	# Check if the time limit has been reached (if you want to keep a time constraint)
	#if {$end_time > 0 && $end >= $end_time} {
	#    break
	#}
    }
    # Write the final "END" line to the CSV file
    puts $fileId0 "0,0,0,0,End of Test"

    # Close the file
    close $fileId0
    specialPrint "SUCCESS" "End Data collection"
    specialPrint "SUCCESS" "CLOSE $::full_xadc_out_file"
}

proc read_data_campaign {end_time} {
    if {![file exists $::full_xadc_out_file]} {
	# If the file doesn't exist, write headers
	set fileId0 [open $::full_ila_out_file_1 "w"]
	puts -nonewline $fileId0 "Times"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "Sample"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "Window"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "heartbeat"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "initialization"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "observation"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "correction"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "classification"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "injection"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "essential"
	puts -nonewline $fileId0 ","
	puts -nonewline $fileId0 "uncorrectable"
	puts $fileId0 " "
	close $fileId0
    }
    if {![file exists $::full_xadc_out_file]} {
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

    #open the file in append mode ("a").
    set fileId1 [open $::full_xadc_out_file "a"]
    set fileId2 [open $::full_ila_out_file_1 "a"]
    specialPrint "INFO" "Read Campaign data"
    specialPrint "REPORT" "OPEN $::full_xadc_out_file"
    specialPrint "REPORT" "OPEN $::full_ila_out_file_1"
    set end 0
    set last_ila_line ""
    while {[checkForStopFlag]} {
	#the number 1000 indicates the loop will be run every second (1000 ms).
	#If you need a higher or lower frequency, adjust it.
	after 1000
	set current_time [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
	refresh_hw_sysmon [get_hw_sysmons]
	puts -nonewline $fileId1 $current_time
	puts -nonewline $fileId1 ","
	#this is the XADC properties that you want to have printed.
	#Add as many as you need.
	set temperature [get_property TEMPERATURE [get_hw_sysmons]]
	puts -nonewline $fileId1 $temperature
	puts -nonewline $fileId1 ","
	set vccaux [get_property VCCAUX [get_hw_sysmons]]
	puts -nonewline $fileId1 $vccaux
	puts -nonewline $fileId1 ","
	set vccbram [get_property VCCBRAM [get_hw_sysmons]]
	puts -nonewline $fileId1 $vccbram
	puts -nonewline $fileId1 ","
	set vccint [get_property VCCINT [get_hw_sysmons]]
	puts $fileId1 $vccint
	specialPrint "DATA"  "time: $current_time | TEMPERATURE : $temperature |VCCAUX: $vccaux |VCCBRAM: $vccbram | VCCINT: $vccint"
	flush stdout
	incr end
	update_ila_cores
	set ila_out_data_1 [upload_hw_ila_data hw_ila_1]
	specialPrint "REPORT"  "Update ILA CSV files"
	write_hw_ila_data -csv_file -force $::full_ila_temp_file_1
	# Open the input CSV file for reading
	set input_file [open $::full_ila_temp_file_1 r]
	# Open the output CSV file for appending
	set output_file [open $::full_ila_out_file_1 a]
	# Skip the header lines in the input CSV file
	for {set i 0} {$i < 2} {incr i} {
	    gets $input_file
	}
	# Read each line from the input CSV file and append it to the output CSV file
	while {[gets $input_file line] != -1} {
	    set loop_time [clock format [clock seconds] -format "%Y-%m-%d %H:%M:%S"]
	    puts $output_file "$loop_time,$line"
	    set last_ila_line "$loop_time,$line"
	    # Split the last line into its individual components
	    set last_line_components [split $last_ila_line ","]
	    if {[lindex $last_line_components 4]} {
		specialPrint "DATA" "time: $loop_time | heartbeat: [lindex $last_line_components 4] | observation: [lindex $last_line_components 6]| correction: [lindex $last_line_components 7]"
	    }
	}
	# Close both files
	close $input_file
	after 3000
	#$::hw_ila_data_1
	# Check if the time limit has been reached (if you want to keep a time constraint)
	#if {$end_time > 0 && $end >= $end_time} {
	#    break
	#}
    }
    # Write the final "END" line to the CSV file
    puts $fileId1 "0,0,0,0,End of Test"
    puts $output_file  "0,0,0,0,0,0,0,0,0,0,0,End of Test"
    # Close the file
    close $fileId1
    close $output_file
    specialPrint "SUCCESS" "End Data collection"
    specialPrint "SUCCESS" "CLOSE $::full_xadc_out_file"
    specialPrint "SUCCESS" "CLOSE $::full_ila_out_file_1"
}

# Define a procedure to create a directory if it doesn't exist
proc create_directory_if_not_exists {dir_path} {
    if {![file exists $dir_path]} {
	file mkdir $dir_path
    }
}

create_directory_if_not_exist $vivado_ip_out_path
set logFileId [open $::out_logFile "w"]
specialPrint "INFO" "Starting Time $::time_now"
specialPrint "INFO" "Creating test files at $::vivado_ip_out_path"

proc check_current_project {} {

    if {[llength [current_project]] == 0} {
	specialPrint "NOTICE"  "Opening The Expected Project "
	open_project $::expectedProjectPath
    } else {
	set currentProject [get_property DIRECTORY [current_project]]
	if {$currentProject ne ""} {
	    set currentProjectFile [file normalize "$currentProject/[get_property NAME [current_project]].xpr"]
	    if {$currentProjectFile eq $::expectedProjectPath} {
		specialPrint "NOTICE"  "The expected project is currently open"
		#disconnect_hw_server
	    } else {
		open_project "$vivado_project_path/$project_name/$project_name.xpr"
	    }
	} else {
	    specialPrint "ERROR"  "Current Project is not Opened"
	    open_project "$vivado_project_path/$project_name/$project_name.xpr"
	}
    }
}

#=======================Open the device=======================================================================
#check_current_project
#disconnect_hw_server
open_hw_manager
connect_hw_server -allow_non_jtag
update_compile_order -fileset sources_1

set hw_targets [get_hw_targets]
set target_device [lindex $hw_targets 0]

open_hw_target [lindex $target_device 0]
specialPrint "INFO" "Opening the Target Device$target_device"
#set target_device "localhost:3121/xilinx_tcf/Digilent/210299B38601"
#open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299B38601}
#open_hw_target {localhost:3121/xilinx_tcf/Digilent/210299B38601}
refresh_hw_device [get_hw_devices xc7a200t_0]

#display_hw_ila_data [ get_hw_ila_data hw_ila_data_1 -of_objects [get_hw_ilas -of_objects [get_hw_devices xc7a200t_0] -filter {CELL_NAME=~"mopshub_board_v2TMR_i/ila_1"}]]

#=======================Read XADC data=======================================================================
#read_xadc 2
#=======================Read Campaign data=======================================================================
read_data_campaign  100
#=======================Read ILA data=======================================================================
update_ila_cores

# Close the hardware connection
#close_hw
disconnect_hw_server
set time_elapsed "[expr {([clock clicks -millisec]-$time_start)/1000.}] sec" ;
set time_end [clock format [clock seconds] -format "%Y-%m-%d_%H:%M:%S"]
specialPrint "INFO" "End Time $time_end"
specialPrint "INFO" "Time elapsed $time_elapsed"
specialPrint "SUCCESS" "CLOSE $::out_logFile"
close $logFileId

