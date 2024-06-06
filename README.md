# MOPS-Hub Readout Software

The MOPS-Hub Readout Software is a Python-based framework designed to control the MOPS-Hub readout board, facilitating comprehensive crate testing and data aggregation. This software package offers modular functionalities and a user-friendly interface for configuring and communicating with the hardware platform.

![MOPS-Hub Readout](https://github.com/ahmedqamesh/mopshub-sw-kcu102/assets/8536649/7ec0939e-345b-4ca1-ac25-7f7bf3cf5020)

## General Features
- Modular framework structured into distinct, self-contained classes for ease of development and maintenance.
- Efficient communication with the MOPS-Hub readout board via TCP/IP connection.
- Configuration management for establishing communication and correct configuration of the hardware.
- Data transmission and reception methods for constructing and transmitting data frames to the IPbus master and processing received data.
- Serial communication capabilities for debugging and interaction with embedded systems.
- Data handling and analysis functionalities, including saving raw data frames to disk in CSV format and offline analysis.

## Installation and Usage

### System Requirements
- **Operating System:** Windows, Linux

### Required Python Packages
- Python 3.x
- Additional packages as specified in the requirements_pip.txt file
- Detailed installation instructions are available on the [Twiki page](https://github.com/ahmedqamesh/mopshub-sw-kcu102/wiki)

### Getting Started
Clone the repository to download the source code:

```
 git clone git@github.com:ahmedqamesh/mopshub-sw-kcu102.git

```
Ensure the MOPS-Hub readout board is connected and the required software dependencies are installed. To test the setup, run the following command in the project directory:

```
python test_mopshub_uhal.py

```
### Configuration and Usage
Detailed instructions for configuration and usage are available in the documentation included in the project repository.

## Contributing and Contact Information:
We welcome contributions from the community please contact : `ahmed.qamesh@cern.ch`.

