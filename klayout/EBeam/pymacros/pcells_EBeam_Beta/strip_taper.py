from . import *
import pya
from SiEPIC.utils import get_technology_by_name, arc_wg_xy
from SiEPIC._globals import PIN_LENGTH as pin_length
from pya import DPolygon

class strip_taper(pya.PCellDeclarationHelper):

    """ 
    Author: Ben Cohen (UBC)
    bcohenkl@ece.ubc.ca
    June 26, 2023

    - This Pcell creates a strip-strip taper 
       - Strip width 1 - w1
       - Strip width 2 - w2
       - Taper Length - taperL 
    """

    def __init__(self):

        # Important: initialize the super class
        super(strip_taper, self).__init__()
        self.technology_name = 'EBeam'
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Parameters
        self.param("w1",     self.TypeDouble, "Waveguide Width 1 [um]",  default = 0.5)
        self.param("w2",     self.TypeDouble, "Waveguide Width 2 [um]",  default = 0.4)
        self.param("taperL", self.TypeDouble, "Taperl Length [um]",      default = 10)

        # Layer Parameters
        self.param("layer",     self.TypeLayer, "Layer",            default = TECHNOLOGY['Si'],                   hidden = True)
        self.param("pinrec",    self.TypeLayer, "PinRec Layer",     default = TECHNOLOGY['PinRec'],               hidden = True)
        self.param("devrec",    self.TypeLayer, "DevRec Layer",     default = TECHNOLOGY['DevRec'],               hidden = True)
        self.param("oxideopen", self.TypeLayer, "Oxide Open Layer", default = TECHNOLOGY['Oxide open (to BOX)'],  hidden = True)



    # Creating the layout
    def produce_impl(self):
        
        # Layout Parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        # Layers
        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Main Ring Parameters
        w1 = self.w1          # Waveguide Width 1[um]
        w2 = self.w2          # Waveguide Width 2[um]
        taperL = self.taperL  # Taper Length [um]

        x = [0, taperL, taperL, 0]     # x-coord
        y = [-w1/2, -w2/2, w2/2, w1/2] # y-coord

        dpts = [pya.DPoint(x[i], y[i]) for i in range(len(x))] # Core body
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon*(1/dbu))
        shapes(LayerSiN).insert(element)

        
        # Pins for mating:
        t = pya.DTrans(pya.Trans.R90, min(x)/dbu, 0/dbu)
        pin = pya.Path([pya.DPoint(0, -pin_length/2), pya.DPoint(0, pin_length/2)], w1/dbu)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("opt1", pya.DTrans(pya.Trans.R0, min(x)/dbu, 0/dbu))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4/dbu
        
        t = pya.DTrans(pya.Trans.R90, max(x)/dbu, 0/dbu)
        pin = pya.Path([pya.DPoint(0, pin_length/2), pya.DPoint(0, -pin_length/2)], w2/dbu)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text("opt2", pya.DTrans(pya.Trans.R90, max(x)/dbu, 0/dbu))
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4/dbu
        
        
        
        # Dev box
        # Encapsulate the pcell within a box for error checking
        dev = pya.DBox(min(x), max(y), max(x), min(y))  
        shapes(LayerDevRecN).insert(dev)