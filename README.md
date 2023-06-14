# mopshub-sw-kcu102

## Getting started
## Installation
 Python 3.6.8 is used here (/usr/bin/python3)
 Compiling and installing from source
 
Instructions
------------

1. **Install the prerequisites**, 
   * **CentOS7**: System version of BOOST, pugiXML & Erlang
     
     .. code-block:: sh
     
		sudo yum -y install make rpm-build git-core erlang gcc-c++ boost-devel pugixml-devel python-devel python3-devel
     
2. **Checkout from git and compile**
     .. code-block:: sh
     
		git clone --depth=1 -b v2.8.9 --recurse-submodules https://github.com/ipbus/ipbus-software.git
		cd ipbus-software
		make PYTHON=/usr/bin/python3.6
3. **Install the software**
	If you’re using an RPM-based linux distribution (e.g. red hat / CentOS), then create and install the RPMs, as follows:
     .. code-block:: sh
		
		sudo make cleanrpm
		make rpm PYTHON=/usr/bin/python3.6
		sudo yum localinstall `find . -iname "*.rpm"`

By default, sudo make install will install uHAL and the ControlHub within /opt/cactus; if you want to install the files in another directory

4. **Set the environment:**
     .. code-block:: sh
		
		export LD_LIBRARY_PATH=/opt/cactus/lib:$LD_LIBRARY_PATH
		export PATH=/opt/cactus/bin:$PATH
## Usage

