# SiEPIC_EBeam_PDK

- <a href="www.siepic.ubc.ca">SiEPIC</a> EBeam PDK, Library - for silicon photonics layout, design and verification
- by Lukas Chrostowski, (c) 2015-2016
- Package for KLayout, klayout.de (developed on KLayout version 0.24.3, OSX)
- Instruction on design, layout, fabrication, test, data analysis for silicon photonics provided in the edX course: <a href="edx.org/course/silicon-photonics-design-fabrication-ubcx-phot1x">Silicon Photonics Design, Fabrication and Data Analysis</a> and textbook <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">Silicon Photonics Design: From Devices to Systems</a> by Lukas Chrostowski and Michael Hochberg.

##Objectives:
 - Use an open-source layout tool (KLayout) to implement a sophisticated layout design environment for silicon photonics
 - Support for both GUI and script-based layout, or combinations of both.
 - Whereas a typical schematic-driven design flow includes a schematic, circuit simulation, layout, and verification (see Chapter 10 of the <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">textbook</a>), the approach taken here is <b>Layout-driven</b>, followed by verification, then a schematic (via a netlist extraction) and simulations.

[![Demo video](http://img.youtube.com/vi/FRmkGjVUIH4/0.jpg)](http://www.youtube.com/watch?v=FRmkGjVUIH4)
[![Lumerical INTERCONNECT simulations](http://img.youtube.com/vi/1bVO4bpiO58/0.jpg)](http://www.youtube.com/watch?v=1bVO4bpiO58)


##Package includes:

- Process Design Kit (PDK): this package, including fabrication documentation, scripts, etc.
- PCells: ring resonator; PCell test structure layout with grating couplers and instantiating the ring resonator PCell.
- Script / Macro to create a layout, including waveguide generation functions.
- GDS Library, updated with marker layers for verification/netlist generation.
- Verification: 
 - Scanning the layout. Finding waveguides, devices, pins.  
 - Verification: Identifying if there are missing connections, mismatched waveguides, too few points in a bend, etc. 
 - Example layouts using the library for verification (EBeam_LukasChrostowski_E_LVS.gds, SiEPIC_EBeam_PDK_Verification_Check.gds).
- Circuit simulations:
 - Netlist generation
 - Creating a Spice netlist suitable for for circuit simulations. This includes extracting the waveguide length (wg_length) for all waveguides.
 - Menu item "Lumerical INTERCONNECT" will automatically: generate the netlist, launch Lumerical INTERCONNECT to perform the circuit simulations, and pop-up a plot of the transmission spectrum.
- Waveguide functionality: 
 - Menu item "W": selected paths are first snapped to the nearest pins, then converted to waveguides.
 - Menu item "Shift-W": selected waveguides are converted back to paths.
- EBeam Layer definitions for KLayout (klayout_Layers_EBeam.lyp).
- Monte Carlo simulations of waveguides.

## Download:

<a href="https://github.com/lukasc-ubc/SiEPIC_EBeam_PDK/archive/master.zip">Zip file download of the PDK</a>

This is posted on GitHub for 1) revision control, 2) so that others can contribute to it, find bugs, 3) easy download of the latest version.

##Installation instructions – for KLayout:
 - Make sure you have <a href="http://www.klayout.de/build.html">KLayout version 0.24.3 or higher</a> installed.  
 - Unzip the PDK.
 - Copy the files from the klayout_dot_config folder (from the zip file) into your KLayout configuration folder: 
  - On Linux and OSX, this is $HOME/.klayout
  - On windows systems, the KLayout configuration folder can be found under C:\Users\YOURUSERNAME\AppData\Roaming\KLayout (64bit)
 - Start KLayout
 - You should:
   - get a message (default layer properties file is not configured).
   - see a top-level menu called “SiEPIC”
   - If you don’t see these, the SiEPIC klayout files are not correctly installed. Go back to the KLayout configuration installation above.
 - File – Setup (Windows) or KLayout – Preferences (OSX)
  - Application – Editing Mode
	  - turn on “Use editing mode by default”
  - Application – Layer Properties
	  - turn on “Use default layer properties file”
	  - click on the “…” to bring up a file finder window, and locate the file “klayout_Layers_EBeam.lyp”
	  - turn on “Automatically add other layers”
  - Ok
 - Quit and restart KLayout
 - Menu SiEPIC – SiEPIC configure shortcut keys  (configures the shortcut keys as per other popular layout tools)

###Installation instructions – for Lumerical INTERCONNECT:
 - To take advantage of the circuit simulations from layout capability, you need <a href=https://www.lumerical.com/tcad-products/interconnect/>Lumerical INTERCONNECT</a>, and then need to install the Compact Model Library (CML) provided here.
 - Install the latest version of the CML (e.g., ebeam_v1.2_2016_01_15.cml) found in the folder "Lumerical_EBeam_CML":
  - Open the INTERCONNECT program, and find the “Element Library” window.
  - Right-click on the “Design kits” folder (at the bottom of the “Elements”) and select “Install”.
  - Select the E-beam CML file for the “Compact Model Library Package” (the CML file from the ZIP archive provided here)
  - Set the “Destination Folder” (any folder on your computer), and then click “OK”.
  - Now the elements should be available in a new “ebeam_v1.2” folder in “Design kits”.
  - To use the E-beam elements, simply drag and drop the elements into the schematic editor.
 - More details on installation instructions and the CML models are provided in the PDF file "ebeam_Lumerical_CML_User_Guide_xxx.pdf". More info on CMLs can be found on <a href="https://kb.lumerical.com/en/pic_cml.html">Lumerical's CML page</a> and <a href="https://kb.lumerical.com/en/ref_install_compact_model_library.html">Lumerical's CML installation page</a>.  For more information about how to use INTERCONNECT, please visit the <a href="https://kb.lumerical.com/en/index.html">Lumerical Knowledge Base</a>.


##Contributing to this project:

 - On the GitHub web page, Fork a copy of the project into your own account.
 - Clone to your Desktop
 - Make edits/contributions.  You can use the KLayout IDE to write Python (or Ruby) scripts; <a href = http://www.klayout.de/doc/about/macro_editor.html>KLayout Python IDE for writing/debugging PCells/scripts/macros</a>.
 - "Commit to master" (your own master)
 - Create a <a href="https://help.github.com/articles/using-pull-requests/">Pull Request</a> -- this will notify me of your contribution, which I can merge into the main project

I am personally using <a href="https://desktop.github.com/">GitHub desktop</a> to synchronize my files. Then I created symbolic links in my .klayout folder to point to the local copy of this repository. This is useful to automatically update my local KLayout installation (e.g., multiple computers), as changes are made in GitHub.

##Screenshots:

![Screenshot1](https://s3.amazonaws.com/edx-course-phot1x-chrostowski/PastedGraphic-9.png)
![Screenshot2](https://s3.amazonaws.com/edx-course-phot1x-chrostowski/PastedGraphic-10.png)
![Screenshot3](https://s3.amazonaws.com/edx-course-phot1x-chrostowski/KLayout_INTERCONNECT.png)

