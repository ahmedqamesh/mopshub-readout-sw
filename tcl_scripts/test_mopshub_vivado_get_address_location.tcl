# 1) Open a TCL Shell using vivado -mode tcl
# 2) source this script
#vivado -mode tcl
# Get the full path of the currently running script
set script_path [file normalize [info script]]
# Extract the directory path from the script path
set root_dir [file dirname $script_path]
# Set the root directory as the current working directory
cd $root_dir
#set project_name "mopshub_board_v3TMR"

#set vivado_project_path     "/home/dcs/git/mopshub/vivado/mopshub_v3TMR"
#set bitstream_golden_file   "$vivado_project_path/$project_name/$project_name.runs/${project_name}_wrapper_golden.bit"

set project_name "mopshub_board_seu"

set vivado_project_path     "/home/dcs/git/mopshub/vivado/mopshub_seu"
set bitstream_golden_file   "$vivado_project_path/$project_name/$project_name.runs/${project_name}_sem_wrapper_fallback.bit"



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

# Initialize start address of the first bitstream
set start_address 0x000000
# Define the number of bitstreams
set num_bitstreams 8

# Loop through each bitstream
for {set i 1} {$i <= $num_bitstreams} {incr i} {
    if {$i == 1} {
        set size_of_current_bitstream $size_of_golden_bitstream_bytes
    } else {
        set size_of_current_bitstream $size_of_feedback_bitstream_bytes
    }
    
    # Calculate the end address for the current bitstream
    set end_address [expr {$start_address + $size_of_current_bitstream}]
    
    # Convert start and end addresses to hexadecimal format
    set start_address_hex [format "0x00%X" $start_address]
    set end_address_hex [format "0x00%X" $end_address]
    
    # Print addresses
    #specialPrint "SUCCESS"   "Bitstream $i:"
    #specialPrint "REPORT"   "Start address: $start_address_hex"
    put "set_property BITSTREAM.CONFIG.NEXT_CONFIG_ADDR $end_address_hex"

    # Update start address for the next bitstream
    set start_address $end_address
}

# Extract Memory information
# Size of a sector in bytes
set sector_size_bytes [expr {4 * 1024}]  ;# 4 KB
# Calculate the number of sectors each bitstream occupies
set sectors_per_bitstream [expr {$size_of_golden_bitstream_bytes / $sector_size_bytes}]

specialPrint "REPORT"  "Bitstream file size: $size_of_golden_bitstream_Mbytes  Mbytes"
# Display the start address of the bitstreams
specialPrint "REPORT" "Sectors per bitstream: $sectors_per_bitstream"
specialPrint "SUCCESS" "Closing the script"	
#write_cfgmem  -format mcs -size 16 -interface SPIx4 -loadbit {up 0x00000000 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_WD_golden.bit" up 0x001A49CC "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x00349398 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x004EDD64 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x00692730 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x008370FC "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x009DBAC8 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" up 0x00B80494 "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper_fallback.bit" } -checksum -force -file "/home/dcs/git/mopshub/vivado/mopshub_seu/mopshub_board_seu/mopshub_board_seu.runs/mopshub_board_seu_sem_WD/mopshub_board_seu_sem_WD_wrapper.mcs"