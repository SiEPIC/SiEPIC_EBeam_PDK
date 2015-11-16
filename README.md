# SiEPIC_EBeam_PDK

- <a href="www.siepic.ubc.ca">SiEPIC</a> EBeam PDK, Library - for silicon photonics layout, design and verification
- by Lukas Chrostowski, (c) 2015
- Package for KLayout, klayout.de (developed on KLayout version 0.24.3, OSX)
- Instruction on design, layout, fabrication, test, data analysis for silicon photonics provided in the edX course: <a href="edx.org/course/silicon-photonics-design-fabrication-ubcx-phot1x">Silicon Photonics Design, Fabrication and Data Analysis</a> and textbook <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">Silicon Photonics Design: From Devices to Systems</a> by Lukas Chrostowski and Michael Hochberg.

##Objectives:
 - Use open-source layout tool (KLayout) to implement a sophisticated layout design environment for silicon photonics
 - Support for both GUI and script-based layout, or combinations of both.
 - Whereas a typical schematic-driven design flow includes a schematic, circuit simulation, layout, and verification (see Chapter 10 of the <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">textbook</a>), the approach taken here is Layout-driven, followed by verification, then a schematic (via a netlist) and simulations.

##Package includes:

- PCells: ring resonator; test structure layout with grating couplers and instantiating the ring resonator.
- Script / Macro to create a layout, including waveguide generation functions.
- GDS Library, updated with marker layers for verification/netlist generation.
- Verification and Netlist generation: 
 - Scanning the layout. Finding waveguides, devices, pins.  
 - Verification: Identifying if there are missing connections, mismatched waveguides, too few points in a bend, etc. 
 - Creating a Spice netlist suitable for importing into Lumerical INTERCONNECT for circuit simulations. Including waveguide length (wg_length) for all waveguides.
 - Example layout using the library for verification (EBeam_LukasChrostowski_E_LVS.gds).
- Waveguide functionality: 
 - Menu item "W": selected paths are first snapped to the nearest pins, then converted to waveguides.
 - Menu item "Shift-W": selected waveguides are converted back to paths.
- EBeam Layer definitions for KLayout (klayout_Layers_EBeam.lyp).

## Download:

<a href="https://github.com/lukasc-ubc/SiEPIC_EBeam_PDK/archive/master.zip">Zip file download of the PDK</a>

This is posted on GitHub for 1) revision control, 2) so that others can contribute to it, find bugs, 3) easy download of the latest version.

##Installation instructions:

 - The files in the klayout_dot_config folder go into your KLayout configuration folder. On Linux and OSX, this is $HOME/.klayout
  - I don’t know what the equivalent is on windows. 
 - Alternatively, you can import all the files one by one using the KLayout IDE.  How to use the <a href = http://www.klayout.de/doc/about/macro_editor.html>KLayout Python IDE for writing/debugging PCells/scripts/macros</a>.
 - For Linux/OSX, you need Python (which comes with the Mac); for Windows, KLayout comes with Python built-in.

I am personally using <a href="https://desktop.github.com/">GitHub desktop</a> to synchronize my files. Then I created symbolic links in my .klayout folder to point to the local copy of this repository. This is useful to automatically update my local KLayout installation (e.g., multiple computers), as changes are made in GitHub.

##Contributing to this project:

 - On the GitHub web page, Fork a copy of the project into your own account.
 - Clone to your Desktop
 - Make edits/contributions
 - "Commit to master" (your own master)
 - Create a <a href="https://help.github.com/articles/using-pull-requests/">Pull Request</a> -- this will notify me of your contribution, which I can merge into the main project

##Screenshots:

![Screenshot1](https://s3.amazonaws.com/edx-course-phot1x-chrostowski/PastedGraphic-9.png)
![Screenshot2](https://s3.amazonaws.com/edx-course-phot1x-chrostowski/PastedGraphic-10.png)
