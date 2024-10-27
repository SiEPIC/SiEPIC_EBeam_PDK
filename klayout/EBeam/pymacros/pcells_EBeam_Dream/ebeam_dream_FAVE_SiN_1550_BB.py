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

        #draw devrec box
        devrec_pts = [
            pya.Point(-100/dbu,50/dbu),
            pya.Point(0,50/dbu),
            pya.Point(0,25/dbu),
            pya.Point(x,1/dbu),
            pya.Point(x,-1/dbu),
            pya.Point(0,-25/dbu),
            pya.Point(0,-50/dbu),
            pya.Point(-100/dbu,-50/dbu),
            ]
        
        #place devrec box
        shapes(LayerDevRecN).insert(pya.Polygon(devrec_pts))


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
        
        '''
        cell_text = ly.create_cell('TEXT', 'Basic',
            {'text':'FAVE:\\nFacet-attached\\nVertical Emitter',
            'layer':self.bb,
            'lspacing':3,
            'mag':9})
        t = pya.Trans(pya.Trans.R0, -98e3, -26e3)
        '''
        cell_text = ly.create_cell('TEXT', 'Basic',
            {'text':'Facet-attached\\nVertical Emitter',
            'layer':self.bb,
            'lspacing':3,
            'mag':9})
        t = pya.Trans(pya.Trans.R0, -98e3, -36e3)
        inst_text = cell.insert(pya.CellInstArray(cell_text.cell_index(), t))

        ly2=pya.Layout()
        ly2.read(filename)
        top_cell = ly2.top_cell()
        top_cell.flatten(True)
        top_cell.transform(pya.Trans(-90e3,28e3))
        self.cell.copy_shapes(top_cell)

        #draw lenses
        width_lens = to_itype(50, dbu)
        length_lens = to_itype(50, dbu)

        for n_ch in range(int(1)):
            lens_pts = [pya.Point(0,-width_lens/2+pitch*n_ch), pya.Point(0,width_lens/2+pitch*n_ch), pya.Point(-length_lens,width_lens/2+pitch*n_ch),pya.Point(-length_lens,-width_lens/2+pitch*n_ch)]
            shapes(LayerBBN).insert(pya.Polygon(lens_pts))
            lens = circle(-length_lens,pitch*n_ch,25/dbu)
            shapes(LayerBBN).insert(pya.Polygon(lens))

            shapes(ly.layer(self.dt)).insert(pya.Box(-100e3,-50e3,0,50e3))

        # Shift cell origin, so that (0,0) is at the pin
        self.cell.transform(pya.Trans(-95e3,0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dream_FAVE_SiN_1550_BB"

