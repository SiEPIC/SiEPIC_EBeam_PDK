# $description: Mach-Zehnder Interferometer (EBeam)
# $show-in-menu
# $group-name: Examples_EBeam
# $menu-path: siepic_menu.exlayout.begin

'''
--- Simple MZI ---

by Lukas Chrostowski, 2020-2024

Example simple script to
 - create a new layout with a top cell
 - create an MZI
 - export to OASIS for submission to fabrication

using SiEPIC-Tools function including connect_pins_with_waveguide and connect_cell

usage:
 - run this script in Python
'''

def MZI():
        
    designer_name = 'Example'
    top_cell_name = 'EBeam_%s_MZI' % designer_name

    import pya
    from pya import Trans, CellInstArray, Text

    import SiEPIC
    from SiEPIC._globals import Python_Env
    from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide, zoom_out, export_layout
    from SiEPIC.utils.layout import new_layout, floorplan
    from SiEPIC.extend import to_itype

    import os

    if Python_Env == 'Script':
        try:
            # For external Python mode, when installed using pip install siepic_ebeam_pdk
            import siepic_ebeam_pdk
        except:
            # Load the PDK from a folder, e.g, GitHub, when running externally from the KLayout Application
            import os, sys
            path_GitHub = os.path.expanduser('~/Documents/GitHub/')
            sys.path.append(os.path.join(path_GitHub, 'SiEPIC_EBeam_PDK/klayout'))
            import siepic_ebeam_pdk

    tech_name = 'EBeam'

    from packaging import version
    if version.parse(SiEPIC.__version__) < version.parse('0.5.1'):
        raise Exception("Errors", "This example requires SiEPIC-Tools version 0.5.1 or greater.")

    '''
    Create a new layout using the EBeam technology,
    with a top cell
    and Draw the floor plan
    '''    
    cell, ly = new_layout(tech_name, top_cell_name, GUI=True, overwrite = True)
    floorplan(cell, 605e3, 410e3)  # units: nanometers

    dbu = ly.dbu

    waveguide_type='Strip TE 1550 nm, w=500 nm'
    waveguide_type_delay='Si routing TE 1550 nm (compound waveguide)'

    # Load cells from library
    if version.parse(SiEPIC.__version__) < version.parse('0.5.19'):
        cell_ebeam_gc = ly.create_cell('GC_TE_1550_8degOxide_BB', tech_name)
        cell_ebeam_y = ly.create_cell('ebeam_y_1550', tech_name)
        cell_ebeam_y_dream = ly.create_cell('ebeam_dream_splitter_1x2_te1550_BB', 'EBeam-Dream')
    else:
        cell_ebeam_gc = ly.create_cell2('GC_TE_1550_8degOxide_BB', tech_name)
        cell_ebeam_y = ly.create_cell2('ebeam_y_1550', tech_name)
        cell_ebeam_y_dream = ly.create_cell2('ebeam_dream_splitter_1x2_te1550_BB', 'EBeam-Dream')

    # grating couplers, place at absolute positions
    x,y = 60000, 15000
    t = pya.Trans(Trans.R0,x,y)
    instGC1 = cell.insert(pya.CellInstArray(cell_ebeam_gc.cell_index(), t))
    t = pya.Trans(Trans.R0,x,y+127000)
    instGC2 = cell.insert(pya.CellInstArray(cell_ebeam_gc.cell_index(), t))

    # automated test label
    text = pya.Text ("opt_in_TE_1550_device_%s_MZI1" % designer_name, t)
    cell.shapes(ly.layer(ly.TECHNOLOGY['Text'])).insert(text).text_size = 5/dbu

    # Y branches:
    # Version 1: place it at an absolute position:
    t = pya.Trans.from_s('r0 %s, %s' % (x+20000,y))
    instY1 = cell.insert(pya.CellInstArray(cell_ebeam_y.cell_index(), t))

    # Version 2: attach it to an existing component, then move relative
    instY2 = connect_cell(instGC2, 'opt1', cell_ebeam_y, 'opt1')
    instY2.transform(Trans(20000,-10000))

    # Waveguides:

    connect_pins_with_waveguide(instGC1, 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instGC2, 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
    inst_wg1 = connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
    inst_wg2 = connect_pins_with_waveguide(instY1, 'opt3', instY2, 'opt2', waveguide_type=waveguide_type,turtle_B=[25,-90])

    # determine path length difference for the MZI

    # Method 1
    def inst_spice_param(inst, param):
        '''
        Input:
            inst: an instance of a cell
            param: which spice parameter you want to query, e.g., param="wg_length"
                the cell needs to have a Text layer containing "spice_param:", e.g., "spice_param:wg_length=100.000 width=0.5"
        Output: 
            the numerical value of the parameter, in microns
        Approach:
            This function scans the GDS layout for a Text label ("spice_param").
            It should work with GDS files create by any tool, 
            as long as it contains the required Text label.
            Alternatively, this could be implemented by querying the PCell directly, but
            this would only work while the script is running.
        '''    
        # get "param" from instance
        params1 = inst.cell.find_components(cell_selected=inst.cell)[0].params
        param_val = dict([p.split('=') for p in params1.split(' ')])[param]
        return float(param_val)*1e6
        
    wg_length1 = inst_spice_param(inst_wg1, 'wg_length')
    wg_length2 = inst_spice_param(inst_wg2, 'wg_length')
    print('Length difference: %s; lengths: %s, %s' % (abs(wg_length2-wg_length1), wg_length2, wg_length1))

    # Method 2
    def wg_length_EBeam(inst):
        '''
        Input: 
            inst: an instance of a "EBeam.Waveguide" PCell
        Output: 
            the waveguide length, in microns
        Approach:
            Use the display title for the cell
            only works inside a scripted layout
        '''
        return float(inst.cell.display_title().split('_')[-1])

    wg_length1 = wg_length_EBeam(inst_wg1)
    wg_length2 = wg_length_EBeam(inst_wg2)
    print('Length difference: %s; lengths: %s, %s' % (abs(wg_length2-wg_length1), wg_length2, wg_length1))


    # 2nd MZI using Dream Photonics 1x2 splitter
    # grating couplers, place at absolute positions
    x,y = 180000, 15000
    t = pya.Trans.from_s('r0 %s,%s' % (x,y))
    instGC1 = cell.insert(pya.CellInstArray(cell_ebeam_gc.cell_index(), t))
    t = pya.Trans.from_s('r0 %s,%s' % (x,y+127000))
    instGC2 = cell.insert(pya.CellInstArray(cell_ebeam_gc.cell_index(), t))

    # automated test label
    text = pya.Text ("opt_in_TE_1550_device_%s_MZI2" % designer_name, t)
    cell.shapes(ly.layer(ly.TECHNOLOGY['Text'])).insert(text).text_size = 5/dbu

    # Y branches:
    instY1 = connect_cell(instGC1, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY1.transform(Trans(20000,0))
    instY2 = connect_cell(instGC2, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY2.transform(Trans(20000,0))

    # Waveguides:

    connect_pins_with_waveguide(instGC1, 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instGC2, 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt3', instY2, 'opt2', waveguide_type=waveguide_type,turtle_B=[25,-90])



    # 3rd MZI, with a very long delay line
    cell_ebeam_delay = ly.create_cell('spiral_paperclip', 'EBeam_Beta',{
                            'waveguide_type':waveguide_type_delay,
                            'length':200,
                            'loops':4,
                            'flatten':True})
    x,y = 60000, 175000
    t = Trans(Trans.R0,x,y)
    instGC1 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))
    t = Trans(Trans.R0,x,y+127000)
    instGC2 = cell.insert(CellInstArray(cell_ebeam_gc.cell_index(), t))

    # automated test label
    text = Text ("opt_in_TE_1550_device_%s_MZI3" % designer_name, t)
    cell.shapes(ly.layer(ly.TECHNOLOGY['Text'])).insert(text).text_size = 5/dbu

    # Y branches:
    instY1 = connect_cell(instGC1, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY1.transform(Trans(20000,0))
    instY2 = connect_cell(instGC2, 'opt1', cell_ebeam_y_dream, 'opt1')
    instY2.transform(Trans(20000,0))

    # Spiral:
    instSpiral = connect_cell(instY2, 'opt2', cell_ebeam_delay, 'optA')
    instSpiral.transform(Trans(20000,0))

    # Waveguides:
    connect_pins_with_waveguide(instGC1, 'opt1', instY1, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instGC2, 'opt1', instY2, 'opt1', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt2', instY2, 'opt3', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY2, 'opt2', instSpiral, 'optA', waveguide_type=waveguide_type)
    connect_pins_with_waveguide(instY1, 'opt3', instSpiral, 'optB', waveguide_type=waveguide_type,turtle_B=[5,-90])



    # Zoom out
    zoom_out(cell)

    # Save with PCell details
    path = os.path.dirname(os.path.realpath(__file__))
    filename = os.path.splitext(os.path.basename(__file__))[0]
    ly.write(os.path.join(path,'..',filename+'.gds'))

    # Export for fabrication:
    file_out = export_layout(cell, path, filename, relative_path = '..', format='oas', screenshot=True)

if __name__ == "__main__":
    MZI()
