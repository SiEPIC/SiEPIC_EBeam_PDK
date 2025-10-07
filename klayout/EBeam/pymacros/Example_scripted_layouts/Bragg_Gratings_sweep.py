# $description: Bragg gratings sweep (EBeam)
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.begin

"""
Bragg Grating Parameter Sweep Layout

by Mustafa Hammood (Mustafa@ece.ubc.ca), 2019
Updated by Lukas Chrostowski, 2025

Creates a complete layout for parameter sweeping Bragg gratings with 3 dB Y-branch splitters.
The script generates an array of devices with selected parameters, grating couplers for testing 
with automated measurement labels, and interleaved waveguide routes between GCs and devices 
for compact routing.

The layout includes:

1. Bragg grating devices with Y-branch splitters
   - Configurable number of periods, grating period, waveguide width
   - Corrugation width sweep capability
   - Support for sinusoidal or rectangular gratings
   - Misalignment parameter for fabrication tolerance studies

2. Grating coupler array for fiber testing
   - Automatically generated based on number of devices
   - 127µm pitch matching standard fiber arrays
   - TE or TM polarization support

3. Interleaved waveguide routing
   - Compact routing for even/odd device numbering
   - Automated measurement labels for each device
   - Supports reflection and transmission measurements

Usage:
 - Requires the SiEPIC-EBeam-PDK
 - Generates a layout with Bragg grating devices and automated test structures
 - Number of devices MUST BE EVEN for interleaved routing configuration
 - Modify Parameters class to customize sweep ranges

Example Parameter Sweeps:
 - Corrugation width: dW from 0 to 0.1 µm (20 devices)
 - Grating period: period from 0.310 to 0.324 µm
 - Number of periods: N from 300 to 700
"""

def Bragg_Gratings_sweep():
    print("SiEPIC_EBeam_PDK: Example - Bragg_Gratings_sweep.py")
    
    import os
    import pya
    from pya import Trans, CellInstArray, Text, DPoint, DPath
    import numpy as np

    import SiEPIC
    from SiEPIC._globals import Python_Env
    from SiEPIC.scripts import zoom_out, export_layout
    from SiEPIC.extend import to_itype
    from SiEPIC.utils.layout import new_layout, floorplan
    from SiEPIC.utils import create_cell2
    from SiEPIC.verification import layout_check

    if Python_Env == 'Script':
        try:
            # For external Python mode, when installed using pip install siepic_ebeam_pdk
            import siepic_ebeam_pdk
        except:
            # Load the PDK from a folder, e.g, GitHub, when running externally from the KLayout Application
            import sys
            path_GitHub = os.path.expanduser('~/Documents/GitHub/')
            sys.path.append(os.path.join(path_GitHub, 'SiEPIC_EBeam_PDK/klayout'))
            import siepic_ebeam_pdk

    tech_name = 'EBeam'

    from packaging import version
    if version.parse(SiEPIC.__version__) < version.parse('0.5.1'):
        raise Exception("Errors", "This example requires SiEPIC-Tools version 0.5.1 or greater.") 

    # ===== Parameters Configuration =====
    # Modify these parameters to customize your Bragg grating sweep
    
    class Parameters():
        """Configuration parameters for Bragg grating device array"""
        
        # ===== Sweep Configuration =====
        # Number of devices MUST BE EVEN for interleaved routing!
        Num_sweep = 10
        
        # ===== Bragg Grating Device Parameters =====
        # Use np.linspace(start, stop, num) to create parameter sweeps
        # Example: np.linspace(0.310, 0.324, 20) creates 20 values from 0.310 to 0.324
        
        N = np.linspace(500, 500, Num_sweep)           # Number of grating periods
        period = np.linspace(.317, .317, Num_sweep)     # Grating period (µm)
        w = np.linspace(.5, .5, Num_sweep)             # Waveguide width (µm)
        dW = np.linspace(0, .1, Num_sweep)             # Corrugation width (µm) - sweep parameter
        sine = 0                                        # Sinusoidal grating (1) or rectangular (0)
        misalignment = np.linspace(0, 0, Num_sweep)    # Misalignment offset (µm)
        
        # ===== Layout and Routing Parameters =====
        device_spacing = 10.5       # Spacing between adjacent devices (µm)
        GC_pitch = 127              # Vertical spacing between grating couplers (µm) - standard fiber array pitch
        GC_offset = 80              # Horizontal spacing between GCs in array (µm)
        GC_device_spacing = 50      # Spacing between GC array and device array (µm)
        
        # Waveguide routing parameters
        wg_bend_radius = 15         # Waveguide route bend radius (µm)
        wg_width = .5               # Waveguide route width (µm)
        wg_pitch = 5                # Spacing between adjacent waveguides (µm) - keep > 3 µm to minimize crosstalk
        route_up = 330              # Y-space from top GC for upward routing (µm)
        route_down = -2*wg_bend_radius  # Y-space from bottom GC for downward routing (µm)
        
        # ===== Device Naming and Technology =====
        name = 'BraggSweep'         # Device name prefix for measurement labels
        pol = 'te'                  # Polarization: 'te' or 'tm'
        PDK = 'EBeam'               # PDK library name
        
        # ===== Layout Size Limits =====
        max_width = 605e3           # Maximum layout width (µm) - standard die width
        max_height = 410e3          # Maximum layout height (µm) - standard die height

    # ===== Layout Generation Class =====
    
    class Layout():
        """Layout generation class for Bragg grating device arrays"""
        
        def __init__(self, params):
            """
            Initialize the Layout class with parameters.
            
            Args:
                params (Parameters): Configuration parameters for the device array
            """
            self.p = params

        def draw_device(self, idx, pos, cell, ly, dbu):
            """
            Draw a single Bragg grating device with Y-branch at specified position.
            
            Args:
                idx (int): Device index in the sweep array
                pos (list): [x, y] position in microns
                cell (pya.Cell): Cell to insert the device into
                ly (pya.Layout): Layout object
                dbu (float): Database unit
            """
            p = self.p
            
            # Bragg grating PCell using create_cell2
            pcell_params = {
                "number_of_periods": int(p.N[idx]), 
                "grating_period": p.period[idx], 
                "wg_width": p.w[idx], 
                "corrugation_width": p.dW[idx], 
                "misalignment": p.misalignment[idx], 
                "sinusoidal": p.sine
            } 
            pcell_bragg = ly.create_cell("ebeam_bragg_te1550", p.PDK, pcell_params)
            
            L_ybranch = 14.8
            H_ybranch = 5.5    
            
            # Place Bragg grating
            x_pos = pos[0]
            y_pos = L_ybranch + pos[1]
            t = Trans(Trans.R90, to_itype(x_pos, dbu), to_itype(y_pos, dbu))
            cell.insert(CellInstArray(pcell_bragg.cell_index(), t))
            
            # Y-branch splitter PCell using create_cell2
            pcell_y = create_cell2(ly, "ebeam_y_1550", p.PDK)
            x_pos = pos[0]
            y_pos = L_ybranch/2 + pos[1]
            t = Trans(Trans.R270, to_itype(x_pos, dbu), to_itype(y_pos, dbu))
            cell.insert(CellInstArray(pcell_y.cell_index(), t))
            
        def draw_device_array(self, cell, ly):
            """
            Draw the complete device array with grating couplers and routing.
            
            This method creates:
            - A sub-cell containing all devices
            - Array of grating couplers for fiber coupling
            - Bragg grating devices with Y-branch splitters
            - Interleaved waveguide routing (even/odd devices)
            - Automated measurement labels for each device
            
            Args:
                cell (pya.Cell): Top cell to insert the device array into
                ly (pya.Layout): Layout object
                
            Returns:
                pya.Cell: The sub-cell containing the device array
            """
            p = self.p
            dbu = ly.dbu
            
            TECHNOLOGY = ly.TECHNOLOGY
            LayerSiN = ly.layer(TECHNOLOGY['Waveguide'])
            TextLayerN = ly.layer(TECHNOLOGY['Text'])
            
            # Clean all cells within the present cell
            ly.prune_subcells(cell.cell_index(), 100)
            
            # Create a sub-cell for the device array
            top_cell = cell
            cell = ly.create_cell(p.name)
            t = Trans(Trans.R0, 0, 0)
            top_cell.insert(CellInstArray(cell.cell_index(), t))    
            
            # Draw grating coupler array using create_cell2
            cell_gc = create_cell2(ly, "ebeam_gc_%s1550" % p.pol, p.PDK)
            GC_imported = cell_gc.cell_index()
            
            # Instantiate GC array (6 rows x Num_sweep/2 columns)
            x = p.GC_offset
            t = Trans(Trans.R0, 0, 0)
            cell.insert(CellInstArray(
                GC_imported, t, 
                DPoint(0, p.GC_pitch/2).to_itype(dbu), 
                DPoint(p.GC_offset, 0).to_itype(dbu), 
                6, int(p.Num_sweep/2)
            ))
            
            L_ybranch = 14.8
            H_ybranch = 5.5
            
            # Draw devices and routing
            for i in range(p.Num_sweep):
                device_xpos = ((p.Num_sweep-2)/2)*p.GC_offset + p.GC_device_spacing + i*p.device_spacing
                device_ypos = 0 
                device_ypos_top = L_ybranch + p.N[i]*p.period[i]

                self.draw_device(i, [device_xpos, device_ypos], cell, ly, dbu)
                
                # Routing for even-indexed devices
                if i % 2 == 0:
                    GC_xpos = p.GC_offset*(p.Num_sweep-2-i)/2

                    # 1st waveguide: bottom GC to reflection port
                    GC_ypos = 0
                    route_ypos = p.route_down - 2*p.wg_pitch*(i+1) + p.wg_pitch
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, route_ypos), 
                        DPoint(device_xpos+H_ybranch/2, route_ypos), 
                        DPoint(device_xpos+H_ybranch/2, device_ypos)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
                    # 2nd waveguide: middle GC to input port (with measurement label)
                    GC_ypos += p.GC_pitch
                    route_ypos = p.route_down - 2*p.wg_pitch*(i) 
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+p.wg_pitch+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+p.wg_pitch+GC_xpos, route_ypos), 
                        DPoint(device_xpos-H_ybranch/2, route_ypos), 
                        DPoint(device_xpos-H_ybranch/2, device_ypos)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
                    # Automated measurement label (laser on Port 2, detectors on Ports 1, 3)
                    t = Trans(Trans.R0, to_itype(GC_xpos, dbu), to_itype(GC_ypos, dbu))
                    polarization = (p.pol).upper()
                    text = Text(
                        "opt_in_%s_1550_%s%dN%dperiod%dw%ddw%dsine%dmisalign" % (
                            polarization, p.name, p.N[i], 1000*p.period[i], 
                            1000*p.w[i], 1000*p.dW[i], p.sine, 1000*p.misalignment[i]
                        ), t
                    )
                    shape = cell.shapes(TextLayerN).insert(text)
                    shape.text_size = 1.5/dbu

                    # 3rd waveguide: top GC to transmission port
                    GC_ypos += p.GC_pitch
                    route_ypos = p.route_up + p.wg_pitch*(i) 
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+p.wg_pitch+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+p.wg_pitch+GC_xpos, route_ypos), 
                        DPoint(device_xpos, route_ypos), 
                        DPoint(device_xpos, device_ypos_top)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
                # Routing for odd-indexed devices
                else:  # i % 2 != 0
                    GC_xpos = p.GC_offset*(p.Num_sweep-1-i)/2

                    # 1st waveguide: bottom GC to reflection port
                    GC_ypos = p.GC_pitch/2
                    route_ypos = p.route_down - 2*p.wg_pitch*(i+1) + 2*p.wg_pitch
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos-p.GC_pitch/4), 
                        DPoint(GC_xpos-p.GC_offset+p.wg_bend_radius+3*p.wg_pitch, GC_ypos-p.GC_pitch/4), 
                        DPoint(GC_xpos-p.GC_offset+p.wg_bend_radius+3*p.wg_pitch, route_ypos),
                        DPoint(device_xpos-H_ybranch/2, route_ypos), 
                        DPoint(device_xpos-H_ybranch/2, device_ypos)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
                    # 2nd waveguide: middle GC to input port (with measurement label)
                    GC_ypos += p.GC_pitch
                    route_ypos = p.route_down - 2*p.wg_pitch*(i) - p.wg_pitch
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos-p.GC_pitch/4), 
                        DPoint(GC_xpos-p.GC_offset+p.wg_bend_radius+2*p.wg_pitch, GC_ypos-p.GC_pitch/4), 
                        DPoint(GC_xpos-p.GC_offset+p.wg_bend_radius+2*p.wg_pitch, route_ypos),
                        DPoint(device_xpos+H_ybranch/2, route_ypos), 
                        DPoint(device_xpos+H_ybranch/2, device_ypos)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
                    # Automated measurement label
                    t = Trans(Trans.R0, to_itype(GC_xpos, dbu), to_itype(GC_ypos, dbu))
                    polarization = (p.pol).upper()
                    text = Text(
                        "opt_in_%s_1550_%s%dN%dperiod%dw%ddw%dsine%dmisalign" % (
                            polarization, p.name, p.N[i], 1000*p.period[i], 
                            1000*p.w[i], 1000*p.dW[i], p.sine, 1000*p.misalignment[i]
                        ), t
                    )
                    shape = cell.shapes(TextLayerN).insert(text)
                    shape.text_size = 1.5/dbu
                    
                    # 3rd waveguide: top GC to transmission port
                    GC_ypos += p.GC_pitch
                    route_ypos = p.route_up + p.wg_pitch*(i) 
                    
                    pts = [
                        DPoint(GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, GC_ypos), 
                        DPoint(p.wg_bend_radius+GC_xpos, route_ypos), 
                        DPoint(device_xpos, route_ypos), 
                        DPoint(device_xpos, device_ypos_top)
                    ]
                    dpath = DPath(pts, p.wg_width)
                    cell.shapes(LayerSiN).insert(dpath.to_itype(dbu))
                    
            return cell

    # ===== Main Layout Generation =====
    
    designer_name = 'Example'
    top_cell_name = 'EBeam_%s_BraggSweep' % designer_name
    
    # Create new layout with EBeam technology
    cell, ly = new_layout(tech_name, top_cell_name, GUI=True, overwrite=True)
    
    # ===== Configure Parameters =====
    
    # Create parameters instance (modify Parameters class above to customize sweep)
    params = Parameters()
    
    # Draw the floorplan matching the size limits
    # Floorplan creates a box from (0,0) to (width, height) on FloorPlan layer (99/0)
    # Make sure FloorPlan layer is visible in the layer panel to see the outline
    inst_fp = floorplan(cell, params.max_width, params.max_height)
    print(f"  Created floorplan: {inst_fp.cell.name}, bbox: {inst_fp.bbox()}")

    # ===== Generate Device Array =====
    
    # Create layout instance and generate device array
    layout = Layout(params)
    layout.draw_device_array(cell, ly)


    # ===== Finalize and Export =====
    
    # Zoom out to see full layout
    zoom_out(cell)

    # Get file paths for export
    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.splitext(os.path.basename(__file__))[0]
    
    # Export for fabrication (OAS format with screenshot)
    file_out = export_layout(cell, path, filename, relative_path='..', format='oas', screenshot=True)

    # Run design rule checking and verification
    file_lyrdb = os.path.join(path, '..', filename + ".lyrdb")
    num_errors = layout_check(cell=cell, verbose=False, GUI=True, file_rdb=file_lyrdb)
    print(f"  Layout verification complete: {num_errors} error(s) found")

    # Show in KLayout Live viewer if running from external Python
    if Python_Env == 'Script':
        from SiEPIC.utils import klive
        klive.show(file_out, lyrdb_filename=file_lyrdb, technology=tech_name)

    # ===== Layout Size Verification =====
    
    # Measure the bounding box of the entire layout
    bbox = cell.bbox()
    layout_width = bbox.width() * ly.dbu  # Convert to microns
    layout_height = bbox.height() * ly.dbu  # Convert to microns
    
    print(f"  Layout bounding box: {bbox}")
    print(f"  Layout size: {layout_width:.1f} µm (width) x {layout_height:.1f} µm (height)")
    print(f"  Size limits: {params.max_width/1e3:.1f} µm (width) x {params.max_height/1e3:.1f} µm (height)")
    
    # Check if layout exceeds size limits
    if layout_width > params.max_width/1e3 or layout_height > params.max_height/1e3:
        error_msg = f"\nERROR: Layout exceeds size limits!\n"
        error_msg += f"  Current size: {layout_width:.1f} µm x {layout_height:.1f} µm\n"
        error_msg += f"  Maximum size: {params.max_width/1e3:.1f} µm x {params.max_height/1e3:.1f} µm\n"
        if layout_width > params.max_width/1e3:
            error_msg += f"  Width exceeds limit by {layout_width - params.max_width/1e3:.1f} µm\n"
        if layout_height > params.max_height/1e3:
            error_msg += f"  Height exceeds limit by {layout_height - params.max_height/1e3:.1f} µm\n"
        error_msg += "\nSuggestions:\n"
        error_msg += "  - Reduce Num_sweep (number of devices)\n"
        error_msg += "  - Reduce device_spacing\n"
        error_msg += "  - Reduce GC_offset or GC_device_spacing\n"
        raise Exception(error_msg)
    else:
        print(f"  ✓ Layout size is within limits")


    print("SiEPIC_EBeam_PDK: Bragg_Gratings_sweep.py - done")
    
    return ly

if __name__ == "__main__":
    Bragg_Gratings_sweep()

