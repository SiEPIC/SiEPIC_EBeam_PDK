import pya
import math
from SiEPIC._globals import PIN_LENGTH as pin_length
from SiEPIC.extend import to_itype
from SiEPIC.scripts import path_to_waveguide, connect_pins_with_waveguide, connect_cell
from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech, get_layout_variables

class ebeam_dream_microlens_edge_couplers_BB(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the ebeam_dream_lens_edge_couplers_BB
    
    Authors: Dream Photonics
    """

    def __init__(self):

        # Important: initialize the super class
        super(ebeam_dream_microlens_edge_couplers_BB, self).__init__()

        self.technology_name = 'EBeam'
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # declare the parameters
        self.param("num_channels", self.TypeInt, "Number of Channels (1 - 16)", default = 1)
        p = self.param("center_wavelength", self.TypeList, "Center Wavelength of Operation [nm]", default = '1550')
        p.add_choice('1550 nm', '1550')
        p.add_choice('1310 nm', '1310')

        self.param("ref_wg", self.TypeBoolean, "Include reference waveguide", default=True)

        #declare the layers
        self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['Si'], hidden=True)
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
        self.param("fibertarget", self.TypeLayer, "Fiber Target Layer", default=TECHNOLOGY['FbrTgt'])
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY['Text'])
        self.param("bb",self.TypeLayer,"BB Layer", default=TECHNOLOGY['BlackBox'])

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


        w_tip = to_itype(0.100,dbu)
        l_taper = to_itype(65,dbu)
        num_channels = self.num_channels
        offset = to_itype(0,dbu)
        pitch = to_itype(127,dbu)
        Lw2 = to_itype(15,dbu)
        Lw3 = Lw2 + to_itype(20,dbu)
        wavelength = int(self.center_wavelength)
        waveguide_type = 'Strip TE 1550 nm, w=500 nm'

        if num_channels < 1:
            num_channels = 1
        if num_channels > 16:
            num_channels = 16

        if wavelength == 1310:
            waveguide_type = 'Strip TE 1310 nm, w=350 nm'
            w_waveguide = to_itype(0.350,dbu)
        elif wavelength == 1550:
            waveguide_type = 'Strip TE 1550 nm, w=500 nm'
            w_waveguide = to_itype(0.500,dbu)


        def circle(x,y,r):
            npts = 180
            theta = 2*math.pi/npts
            pts = []
            for i in range(0,npts):
              pts.append(pya.Point.from_dpoint(pya.DPoint((x+r*math.cos(i*theta))/1,(y+r*math.sin(i*theta))/1)))
            return pts

        #draw one loopback device
        if self.ref_wg:
            for ref_loop in range(2):
                #draw fibre target circle
                align_circle = circle(offset,-pitch*(ref_loop+1),2/dbu)
                #place fibre target circle
                shapes(LayerFbrTgtN).insert(pya.Polygon(align_circle))

        if self.ref_wg:
            #create waveguide to for loopback
            loopback_path = pya.DPath([pya.DPoint(0,-127),pya.DPoint((offset + l_taper + Lw2)*dbu+15,-127),pya.DPoint((offset + l_taper + Lw2)*dbu+15,-254),pya.DPoint(0,-254)],0.5)
            self.layout.technology_name = self.technology_name #required otherwise "create_cell" doesn't load
            pcell = self.layout.create_cell("Waveguide",self.technology_name,{"path": loopback_path, "waveguide_type": waveguide_type})
            t = pya.Trans(pya.Trans.R0,0,0)
            self.cell.copy(pcell,LayerSiN,LayerBBN)
            wg = self.cell.insert(pya.CellInstArray(pcell.cell_index(),t))
            wg.flatten()
            self.cell.clear(LayerDevRecN)
            self.cell.clear(LayerPinRecN)
            self.cell.clear(LayerSiN)


        ##########################################################################################################################################################################
        #draw N tapers
        for n_ch in range(int(num_channels)):

            #draw the taper
            taper_pts = [pya.Point(0,-w_waveguide/2+pitch*n_ch),pya.Point(0,w_waveguide/2+pitch*n_ch),pya.Point(offset + l_taper + Lw3,w_waveguide/2+pitch*n_ch),pya.Point(offset + l_taper + Lw3,-w_waveguide/2+pitch*n_ch)]

            #place the taper
            shapes(LayerBBN).insert(pya.Polygon(taper_pts))

            #draw and place pin on the waveguide:
            x = offset + l_taper + Lw3
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
        if self.ref_wg:
            devrec_pts = [pya.Point(0,pitch*n_ch+30/dbu),pya.Point(x,pitch*n_ch+30/dbu),pya.Point(x,-pitch*2-30/dbu),pya.Point(0,-pitch*2-30/dbu)]
        else:
            devrec_pts = [pya.Point(0,pitch*n_ch+30/dbu),pya.Point(x,pitch*n_ch+30/dbu),pya.Point(x,-30/dbu),pya.Point(0,-30/dbu)]
        
        #place devrec box
        shapes(LayerDevRecN).insert(pya.Polygon(devrec_pts))

        #edge of chip text
        t = pya.Trans(pya.Trans.R0,0,1/dbu)
        text = pya.Text("<- Edge of chip",t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 3/dbu

        #BB description
        t = pya.Trans(pya.Trans.R0,0,-15/dbu)
        text = pya.Text("  Number of Channel(s): " + str(num_channels) + "\n  Center Wavelength: " + str(wavelength) + " nm",t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 3/dbu

        #BB description
        t = pya.Trans(pya.Trans.R0, 0,-25/dbu)
        text = pya.Text("<- 25 MFD lens",t)
        shape = shapes(LayerTEXTN).insert(text)
        shape.text_size = 3/dbu

        #draw DP BB logo
        import os
        dir_path = os.path.normpath(os.path.join(os.path.dirname(os.path.realpath(__file__)), "../../gds/EBeam_Dream/"))
        filename = os.path.join(dir_path, 'DP_lens_BB_logo.gds')

        ly2=pya.Layout()
        ly2.read(filename)
        top_cell = ly2.top_cell()
        top_cell.flatten(True)
        self.cell.copy_shapes(top_cell)

        #draw lenses
        width_lens = to_itype(50, dbu)
        length_lens = to_itype(50, dbu)

        if self.ref_wg:
            for n_ch in range(int(num_channels+2)):
                lens_pts = [pya.Point(0,-width_lens/2+pitch*n_ch-2*pitch), pya.Point(0,width_lens/2+pitch*n_ch-2*pitch), pya.Point(-length_lens,width_lens/2+pitch*n_ch-2*pitch),pya.Point(-length_lens,-width_lens/2+pitch*n_ch-2*pitch)]
                shapes(LayerBBN).insert(pya.Polygon(lens_pts))
                lens = circle(-length_lens,pitch*n_ch-2*pitch,25/dbu)
                shapes(LayerBBN).insert(pya.Polygon(lens))
        else:
            for n_ch in range(int(num_channels)):
                lens_pts = [pya.Point(0,-width_lens/2+pitch*n_ch), pya.Point(0,width_lens/2+pitch*n_ch), pya.Point(-length_lens,width_lens/2+pitch*n_ch),pya.Point(-length_lens,-width_lens/2+pitch*n_ch)]
                shapes(LayerBBN).insert(pya.Polygon(lens_pts))
                lens = circle(-length_lens,pitch*n_ch,25/dbu)
                shapes(LayerBBN).insert(pya.Polygon(lens))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ebeam_dream_microlens_edge_couplers_%s_%s_BB" % (
            self.center_wavelength,
            self.num_channels,
        )

