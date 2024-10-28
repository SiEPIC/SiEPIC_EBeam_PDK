import pya
import math
from SiEPIC._globals import PIN_LENGTH as pin_length
from SiEPIC.extend import to_itype
from SiEPIC.scripts import path_to_waveguide, connect_pins_with_waveguide, connect_cell
from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech, get_layout_variables

class ebeam_dream_FAVE_SiN_1550_BB(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the Dream Photonics 
    Facet-attached Vertical Emitter(FAVE)
    for Silicon Nitride
    for 1550 nm operation
    
    Authors: Dream Photonics
    """

    def __init__(self):

        # Important: initialize the super class
        super(ebeam_dream_FAVE_SiN_1550_BB, self).__init__()

        self.technology_name = 'EBeam'
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        #declare the layers
        self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['SiN'], hidden=False)
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'], hidden=True)
        self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'], hidden=True)
        self.param("fibertarget", self.TypeLayer, "Fiber Target Layer", default=TECHNOLOGY['FbrTgt'], hidden=True)
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['Text'], hidden=True)
        self.param("bb",self.TypeLayer,"BB Layer", default=TECHNOLOGY['BlackBox'], hidden=True)
        self.param("dt",self.TypeLayer,"DT Layer", default=TECHNOLOGY['Deep Trench'], hidden=True)
        self.param("dt_bezier_corner",self.TypeDouble,"Rounded corners (Bezier) fraction, 0 to 1, (0=off)", default=0.2, hidden=False)

    def can_create_from_shape_impl(self):
        return False


    def produce(self, layout, layers, parameters, cell):
        # This is the main part of the implementation: create the layout
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        #fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        
        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        LayerFbrTgtN = ly.layer(self.fibertarget)
        LayerTEXTN = ly.layer(self.textl)
        LayerBBN = ly.layer(self.bb)

        offset = to_itype(0,dbu)
        pitch = to_itype(127,dbu)
        l_taper = 60e3
        Lw2 = to_itype(15,dbu)
        Lw3 = Lw2 + to_itype(20,dbu)

        wavelength = 1550

        waveguide_type = 'SiN Strip TE 1550 nm, w=750 nm'
        w_waveguide = 750 # nm

        def circle(x,y,r):
            npts = 50
            theta = 2*math.pi/npts
            pts = []
            for i in range(0,npts):
              pts.append(pya.Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1,(y+r*math.sin(i*theta))/1)))
            return pts


        ##########################################################################################################################################################################
        #draw N tapers
        x = offset + l_taper + Lw3
        for n_ch in range(1):

            #draw the taper
            taper_pts = [pya.Point(0,-w_waveguide/2+pitch*n_ch),pya.Point(0,w_waveguide/2+pitch*n_ch),pya.Point(offset + l_taper + Lw3,w_waveguide/2+pitch*n_ch),pya.Point(offset + l_taper + Lw3,-w_waveguide/2+pitch*n_ch)]

            #place the taper
            shapes(LayerBBN).insert(pya.Polygon(taper_pts))

            #draw and place pin on the waveguide:
            t = pya.Trans(pya.Trans.R0, x, pitch*n_ch)
            pin = pya.Path([pya.Point(-pin_length/2,0),pya.Point(pin_length/2,0)], w_waveguide)
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text(f"opt{n_ch+1}",t)
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 3/dbu
   
            #draw fibre target circle
            align_circle = circle(offset,pitch*n_ch,2/dbu)

            #place fibre target circle
            shapes(LayerFbrTgtN).insert(pya.Polygon(align_circle))


        #BB description
        t = pya.Trans(pya.Trans.R0,0,-15/dbu)
        text = pya.Text("  Waveguide type: " + 'SiN' + "\n  Wavelength: " + str(wavelength) + " nm",t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 3/dbu

        #BB description
        t = pya.Trans(pya.Trans.R0, 0,-25/dbu)
        text = pya.Text("  25 micron MFD Facet-attached\n  Vertical Emitter (FAVE)",t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 3/dbu

        #draw DP BB logo
        import os
        dir_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../gds/EBeam_Dream/"))
        filename = os.path.join(dir_path, 'DP_logo.gds')
        
        cell_text = ly.create_cell('TEXT', 'Basic',
            {'text':'  Facet-attached\\n Vertical Emitter',
            'layer':self.bb,
            'lspacing':3,
            'mag':9})
        t = pya.Trans(pya.Trans.R0, -98e3, -33e3)
        inst_text = cell.insert(pya.CellInstArray(cell_text.cell_index(), t))

        ly2=pya.Layout()
        ly2.read(filename)
        top_cell = ly2.top_cell()
        top_cell.flatten(True)
        top_cell.transform(pya.Trans(-91e3,27e3))
        self.cell.copy_shapes(top_cell)

        # draw lens
        width_lens = to_itype(50, dbu)
        length_lens = to_itype(50, dbu)
        n_ch = 0
        lens_pts = [pya.Point(0,-width_lens/2+pitch*n_ch), pya.Point(0,width_lens/2+pitch*n_ch), pya.Point(-length_lens,width_lens/2+pitch*n_ch),pya.Point(-length_lens,-width_lens/2+pitch*n_ch)]
        shapes(LayerBBN).insert(pya.Polygon(lens_pts))
        lens = circle(-length_lens,pitch*n_ch,25/dbu)
        shapes(LayerBBN).insert(pya.Polygon(lens))

        # Draw Deep Trench
        # Use Bezier corners for aesthetic purposes, 
        #   and perhaps for better fabrication outcomes
        width, height = 100e3, 100e3
        if self.dt_bezier_corner == 0:
            polygon = pya.Box(-width,-height/2,0,height/2)
        else:
            from SiEPIC.utils.geometry import box_bezier_corners
            polygon = box_bezier_corners(width*dbu, height*dbu, self.dt_bezier_corner).to_itype(dbu).transformed(pya.Trans(-width/2,0))
        shapes(ly.layer(self.dt)).insert(polygon)

        #draw devrec box
        devrec_pts = [
            pya.Point(0,25/dbu),
            pya.Point(x,1/dbu),
            pya.Point(x,-1/dbu),
            pya.Point(0,-25/dbu),
            ]
        #place devrec box
        # merge
        
        shapes(LayerDevRecN).insert(
            (pya.Region(pya.Polygon(devrec_pts)) + 
            pya.Region(polygon)).merge()
            )


        # Shift cell origin, so that (0,0) is at the pin
        self.cell.transform(pya.Trans(-95e3,0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dream_FAVE_SiN_1550_BB"





class test_lib(pya.Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("ebeam_dream_FAVE_SiN_1550_BB", ebeam_dream_FAVE_SiN_1550_BB())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: ebeam_dream_FAVE_SiN_1550_BB")

    from SiEPIC.utils.layout import new_layout
    from SiEPIC.scripts import zoom_out
    from SiEPIC._globals import Python_Env

    if Python_Env == 'Script':
        # For external Python mode, when installed using pip install siepic_ebeam_pdk
        import siepic_ebeam_pdk
    
    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Instantiate, with default parameters
    pcell = ly.create_cell("ebeam_dream_FAVE_SiN_1550_BB", library, {})
    t = pya.Trans(pya.Trans.R0, 0, 0)
    topcell.insert(pya.CellInstArray(pcell.cell_index(), t))

    # Instantiate, with default parameters
    pcell = ly.create_cell("ebeam_dream_FAVE_SiN_1550_BB", library, {'dt_bezier_corner':0})
    t = pya.Trans(pya.Trans.R0, 0, 125e3)
    topcell.insert(pya.CellInstArray(pcell.cell_index(), t))

    zoom_out(topcell)

    # Export for fabrication, removing PCells
    import os
    from SiEPIC.scripts import export_layout
    thisfilepath = os.path.dirname(os.path.realpath(__file__))
    filename, extension = os.path.splitext(os.path.basename(__file__))
    file_out = export_layout(topcell, thisfilepath, filename, relative_path = '', format='oas', screenshot=True)

    # Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
    if Python_Env == 'Script':
        from SiEPIC.utils import klive
        klive.show(file_out,  technology=tech)
