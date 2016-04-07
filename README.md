# SiEPIC_EBeam_PDK

- <a href="www.siepic.ubc.ca">SiEPIC</a> EBeam PDK, Library - for silicon photonics layout, design, verification and circuit simulation
- by Lukas Chrostowski, (c) 2015-2016
- Package for KLayout, klayout.de (developed on KLayout version 0.24.3, OSX)
- Instruction on design, layout, fabrication, test, data analysis for silicon photonics provided in the edX course: <a href="http://edx.org/course/silicon-photonics-design-fabrication-ubcx-phot1x">Silicon Photonics Design, Fabrication and Data Analysis</a> and textbook <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">Silicon Photonics Design: From Devices to Systems</a> by Lukas Chrostowski and Michael Hochberg.
- Fabrication runs via Electron Beam Lithography are available, including <a href="https://www.linkedin.com/pulse/openebl-fabrication-test-passive-silicon-photonic-lukas-chrostowski">openEBL</a> fabrication.

##Download and Installation instructions:
 - <a href="https://github.com/lukasc-ubc/SiEPIC_EBeam_PDK/wiki/Installation-instructions">SiEPIC_EBeam_PDK download and installation instructions</a> on the wiki page.  

 
##Objectives:
 - Use an open-source layout tool (KLayout) to implement a sophisticated layout design environment for silicon photonics
 - Support for both GUI and script-based layout, or combinations of both.
 - KLayout-INTERCONNECT integration offers a layout-first design methodology. Inspired by Layout Versus Schematic tools, this PDK includes netlist extraction routines to generate a schematic from the layout. This allows the user to directly simulate from the layout, without needing to create the schematic first. This approach is possibly more appealing to photonics designers who are accustomed to designing physical layouts, rather than schematics. A library of components (layout and compact models) is included in the Process Design Kit, specifically for silicon photonics fabrication via Electron Beam Lithography.
 - Whereas a typical schematic-driven design flow includes a schematic, circuit simulation, layout, and verification (see Chapter 10 of the <a href="http://www.cambridge.org/ca/academic/subjects/engineering/electronic-optoelectronic-devices-and-nanotechnology/silicon-photonics-design-devices-systems">textbook</a>), the approach taken here is <b>Layout-driven</b>, followed by verification, then a schematic (via a netlist extraction) and simulations.
 - Read more details in our two SPIE papers: <a href="http://mina.ubc.ca/ref_design-and-simulation-sili">Design and simulation of silicon photonic schematics and layouts</a> and <a href="http://mina.ubc.ca/ref_schematic-driven-silicon-p">Schematic Driven Silicon Photonics Design</a>.

[![Demo video](http://img.youtube.com/vi/FRmkGjVUIH4/0.jpg)](http://www.youtube.com/watch?v=FRmkGjVUIH4)
[![Lumerical INTERCONNECT simulations](http://img.youtube.com/vi/1bVO4bpiO58/0.jpg)](http://www.youtube.com/watch?v=1bVO4bpiO58)
Video of a layout and simulation of a ring resonator circuit:
[![Layout and simulation of a ring resonator circuit](http://img.youtube.com/vi/1E47VP6Fod0/0.jpg)](https://www.youtube.com/watch?v=1E47VP6Fod0)
Monte Carlo simulations of a ring resonator circuit, showing fabrication variations:
[![Monte Carlo simulations of a ring resonator circuit](http://img.youtube.com/vi/gUiBsVRlzPE/0.jpg)](https://www.youtube.com/watch?v=gUiBsVRlzPE)



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
 - Hot Key "W": selected paths are first snapped to the nearest pins, then converted to waveguides.
 - Hot Key "Shift-W": selected waveguides are converted back to paths.
- Layout object snapping
 - Hot Key "Shift-O": Snaps the selected object to the one where the mouse is hovering over.
- EBeam Layer definitions for KLayout (klayout_Layers_EBeam.lyp).
- Monte Carlo simulations of waveguides, ring resonators built using directional couplers, y-branches.




##Contributing to this project:

You can download the latest development version (master) of the PDK: <a href="https://github.com/lukasc-ubc/SiEPIC_EBeam_PDK/archive/master.zip">Zip file download of the PDK</a>

It is posted on GitHub for 1) revision control, 2) so that others can contribute to it, find bugs, 3) easy download of the latest version.

To contribute to the PDK:
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

