from . import *

class strip_to_slot(pya.PCellDeclarationHelper):
  """
  The PCell declaration for the strip_to_slot.
  draft by Lukas Chrostowski july 24, 2017
  based on https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-21-16-19029&id=259920
  """

  def __init__(self):

    # Important: initialize the super class
    super(strip_to_slot, self).__init__()
    TECHNOLOGY = get_technology_by_name('EBeam')

    # declare the parameters
    self.param("silayer", self.TypeLayer, "Si Layer", default = TECHNOLOGY['Waveguide'])
    self.param("r", self.TypeDouble, "Radius", default = 10)
    self.param("w", self.TypeDouble, "Waveguide Width", default = 0.5)
    self.param("g", self.TypeDouble, "Gap", default = 0.2)
    self.param("Lc", self.TypeDouble, "Coupler Length", default = 0.0)
    self.param("orthogonal_identifier", self.TypeInt, "Orthogonal identifier (1=TE, 2=TM)", default = 1)     
    self.param("pinrec", self.TypeLayer, "PinRec Layer", default = TECHNOLOGY['PinRec'])
    self.param("devrec", self.TypeLayer, "DevRec Layer", default = TECHNOLOGY['DevRec'])
    self.param("textl", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))

  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "strip_to_slot(R=" + ('%.3f' % self.r) + ",g=" + ('%g' % (1000*self.g)) + ",Lc=" + ('%g' % (1000*self.Lc)) + ",orthogonal_identifier=" + ('%s' % self.orthogonal_identifier) + ")"

  def can_create_from_shape_impl(self):
    return False
    
  def produce_impl(self):
    # This is the main part of the implementation: create the layout

    from math import pi, cos, sin
    from SiEPIC.utils import arc, arc_xy

    # fetch the parameters
    dbu = self.layout.dbu
    ly = self.layout
    shapes = self.cell.shapes
    
    LayerSi = self.silayer
    LayerSiN = ly.layer(LayerSi)
    LayerPinRecN = ly.layer(self.pinrec)
    LayerDevRecN = ly.layer(self.devrec)
    TextLayerN = ly.layer(self.textl)

    
    w = int(round(self.w/dbu))
    r = int(round(self.r/dbu))
    g = int(round(self.g/dbu))
    Lc = int(round(self.Lc/dbu))

    # draw the half-circle
    x = 0
    y = r+0.35/dbu+g
#    layout_arc_wg_dbu(self.cell, LayerSiN, x-Lc/2, y, r, w, 180, 270)
    #layout_arc_wg_dbu(self.cell, LayerSiN, x+Lc/2, y, r, 0.2/dbu, 270, 360)

    t = Trans(Trans.R0,x+Lc/2, y)
    self.cell.shapes(LayerSiN).insert(Path(arc(r, 270, 360),0.2/dbu).transformed(t).simple_polygon())

    # Draw 500 to 200 nm polygon
    pts = []
    pts.append(Point.from_dpoint(DPoint(0/dbu, (-0.35+0.6)/dbu)))
    pts.append(Point.from_dpoint(DPoint(0/dbu, (-0.85+0.6)/dbu)))
    pts.append(Point.from_dpoint(DPoint(-10/dbu, (-0.55+0.6)/dbu)))
    pts.append(Point.from_dpoint(DPoint(-10/dbu, (-0.35+0.6)/dbu)))
    polygon = Polygon(pts)
    shapes(LayerSiN).insert(polygon)

    # Create the top left 1/2 waveguide
    wg1 = Box(-10/dbu, (-0.35+0.6+0.3)/dbu, 0, (-0.55+0.6+0.3)/dbu)
    shapes(LayerSiN).insert(wg1)

    
    # Create the pins, as short paths:
    from SiEPIC._globals import PIN_LENGTH 
 
    # Create the waveguide
    wg1 = Box(0, -w/2, r+w/2+w+Lc/2, w/2)
    shapes(LayerSiN).insert(wg1)

    # Pins on the bus waveguide side:
    pin = Path([Point(-10.1/dbu, (-0.35+0.6+0.05)/dbu), Point(-9.9/dbu, (-0.35+0.6+0.05)/dbu)], w)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, -10/dbu, (-0.35+0.6+0.05)/dbu)
    text = Text ("pin1", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    pin = Path([Point(r+w/2+w-PIN_LENGTH/2+Lc/2, 0), Point(r+w/2+w+PIN_LENGTH/2+Lc/2, 0)], w)
    shapes(LayerPinRecN).insert(pin)
    t = Trans(Trans.R0, r+w/2+w+Lc/2, 0)
    text = Text ("pin2", t)
    shape = shapes(LayerPinRecN).insert(text)
    shape.text_size = 0.4/dbu

    # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
    dev = Box(-10/dbu, -w/2-w, r+w/2+w+Lc/2, y )
    shapes(LayerDevRecN).insert(dev)

    print("Done drawing the layout for - strip_to_slot: %.3f-%g" % ( self.r, self.g) )
