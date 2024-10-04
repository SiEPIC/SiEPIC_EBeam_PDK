"""
This file is part of the SiEPIC-EBeam-PDK

Version history:

Lukas Chrostowski 2022/04/01
 - PCell takes an input of the waveguide type from a dropdown list, rather than
   detailed parameters.  Loaded from Waveguides.xml
"""

from pya import *
import pya


class Waveguide(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(Waveguide, self).__init__()

        from SiEPIC.utils import load_Waveguides_by_Tech

        """
    # https://github.com/KLayout/klayout/issues/879
    tech = self.layout.library().technology
    if not tech:
       tech = 'EBeam'
    self.technology_name = tech
    """
        self.technology_name = "EBeam"

        # Load all strip waveguides
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)

        # declare the parameters

        p = self.param(
            "waveguide_type",
            self.TypeList,
            "Waveguide Type",
            default=self.waveguide_types[0]["name"],
        )
        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])
        self.param(
            "path",
            self.TypeShape,
            "Path",
            default=DPath([DPoint(0, 0), DPoint(10, 0), DPoint(10, 10)], 0.5),
        )

        # self.param("length", self.TypeDouble, "Length", default = 0, readonly=True)
        """ todo - can add calculated values and parameters for user info
    self.param("radius", self.TypeDouble, "Bend Radius", default = 0, readonly=True)
    """

        self.cellName = "Waveguide"

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        if "waveguide_length" in dir(self):
            return "%s_%s_%.3f" % (
                self.cellName,
                self.waveguide_type.replace(" ", "_").replace(",", ""),
                self.waveguide_length,
            )
        else:
            return "%s_%s_%.3f" % (
                self.cellName,
                self.waveguide_type.replace(" ", "_").replace(",", ""),
                0,
            )

    def coerce_parameters_impl(self):
        #    self.length = self.waveguide_length
        pass

    def can_create_from_shape_impl(self):
        return self.shape.is_path()

    def transformation_from_shape_impl(self):
        return Trans(Trans.R0, 0, 0)

    def parameters_from_shape_impl(self):
        self.path = self.shape.path

    def produce_impl(self):
        # https://github.com/KLayout/klayout/issues/879
        # tech = self.layout.library().technology

        # Make sure the technology name is associated with the layout
        #  PCells don't seem to know to whom they belong!
        if self.layout.technology_name == "":
            self.layout.technology_name = self.technology_name

        # Draw the waveguide geometry, new function in SiEPIC-Tools v0.3.90
        from SiEPIC.utils.layout import layout_waveguide4

        self.waveguide_length = layout_waveguide4(
            self.cell, self.path, self.waveguide_type, debug=False
        )

        # print("EBeam.%s: length %.3f um, complete" % (self.cellName, self.waveguide_length))


"""
import pya
from pya import *

class Waveguide(pya.PCellDeclarationHelper):

  def __init__(self):
    # Important: initialize the super class
    super(Waveguide, self).__init__()
    # declare the parameters
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    self.param("path", self.TypeShape, "Path", default = DPath([DPoint(0,0), DPoint(10,0), DPoint(10,10)], 0.5))
    self.param("radius", self.TypeDouble, "Radius", default = 5)
    self.param("width", self.TypeDouble, "Width", default = 0.5)
    self.param("adiab", self.TypeBoolean, "Adiabatic", default = False)
    self.param("bezier", self.TypeDouble, "Bezier Parameter", default = 0.35)
    self.param("layers", self.TypeList, "Layers", default = ['Waveguide'])
    self.param("widths", self.TypeList, "Widths", default =  [0.5])
    self.param("offsets", self.TypeList, "Offsets", default = [0])
    self.param("CML", self.TypeString, "Compact Model Library (CML)", default = 'EBeam')
    self.param("model", self.TypeString, "CML Model name", default = 'ebeam_wg_integral_1550') 
    self.cellName="Waveguide"
    
  def display_text_impl(self):
    # Provide a descriptive text for the cell
    return "%s_%s" % (self.cellName, self.path)
  
  def coerce_parameters_impl(self):
    from SiEPIC.extend import to_itype
    print("EBeam.Waveguide coerce parameters")
    
    if 0:
        TECHNOLOGY = get_technology_by_name('EBeam')
        dbu = self.layout.dbu
        wg_width = to_itype(self.width,dbu)
        for lr in range(0, len(self.layers)):
          layer = self.layout.layer(TECHNOLOGY[self.layers[lr]])
          width = to_itype(self.widths[lr],dbu)
          # check to make sure that the waveguide with parameters are consistent in both places
          if self.layout.layer(TECHNOLOGY['Waveguide']) == layer:
            if width != wg_width:
              self.widths[lr] = self.width
          # check to make sure that the DevRec is bigger than the waveguide width
          if self.layout.layer(TECHNOLOGY['DevRec']) == layer:
            if width < wg_width:
              self.widths[lr] = self.width*2
              
  def can_create_from_shape_impl(self):
    return self.shape.is_path()

  def transformation_from_shape_impl(self):
    return Trans(Trans.R0,0,0)

  def parameters_from_shape_impl(self):
    self.path = self.shape.dpath
        
  def produce_impl(self):

    from SiEPIC.utils.layout import layout_waveguide2
    from SiEPIC.utils import  angle_vector
    from math import cos, sin, pi, sqrt
    import pya
    from SiEPIC.extend import to_itype
    
    # print("EBeam.Waveguide")
    
    from SiEPIC.utils import get_technology_by_name
    TECHNOLOGY = get_technology_by_name('EBeam')
    
    dbu = self.layout.dbu
    wg_width = to_itype(self.width,dbu)
    path = self.path.to_itype(dbu)

    if not (len(self.layers)==len(self.widths) and len(self.layers)==len(self.offsets) and len(self.offsets)==len(self.widths)):
      raise Exception("There must be an equal number of layers, widths and offsets")
    path.unique_points()
    pts = path.get_points()
    
    # Draw the waveguide geometry, new in SiEPIC-Tools v0.3.64
    waveguide_length = layout_waveguide2(TECHNOLOGY, self.layout, self.cell, self.layers, self.widths, self.offsets, pts, self.radius, self.adiab, self.bezier)

    pts = path.get_points()
    LayerPinRecN = self.layout.layer(TECHNOLOGY['PinRec'])
    
    t1 = Trans(angle_vector(pts[0]-pts[1])/90, False, pts[0])
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-5, 0), Point(5, 0)], wg_width).transformed(t1))
    self.cell.shapes(LayerPinRecN).insert(Text("pin1", t1, 0.3/dbu, -1))
    
    t = Trans(angle_vector(pts[-1]-pts[-2])/90, False, pts[-1])
    self.cell.shapes(LayerPinRecN).insert(Path([Point(-5, 0), Point(5, 0)], wg_width).transformed(t))
    self.cell.shapes(LayerPinRecN).insert(Text("pin2", t, 0.3/dbu, -1))

    LayerDevRecN = self.layout.layer(TECHNOLOGY['DevRec'])

    # Compact model information
    angle_vec = angle_vector(pts[0]-pts[1])/90
    halign = 0 # left
    angle=0
    if angle_vec == 0: # horizontal
      halign = 2 # right
      angle=0
      dpt = Point(0, 0.2*wg_width)
    if angle_vec == 2: # horizontal
      halign = 0 # left
      angle = 0
      dpt=Point(0, 0.2*wg_width)
    if angle_vec == 1: # vertical
      halign = 2 # right
      angle = 1
      dpt=Point(0.2*wg_width,0)
    if angle_vec == -1: # vertical
      halign = 0 # left
      angle = 1
      dpt=Point(0.2*wg_width,0)
    pt2=pts[0] + dpt
    pt3=pts[0] - dpt
    pt4=pts[0] - 2*dpt
    pt5=pts[0] + 2*dpt
      

    t = Trans(angle, False, pt5)
    text = Text ('cellName=%s' % self.cellName, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt3) 
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/%s' % self.CML, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt2)
    text = Text ('Component=%s' % self.model, t, 0.1*wg_width, -1)
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pts[0])
    pts_txt = str([ [round(p.to_dtype(dbu).x,3), round(p.to_dtype(dbu).y,3)] for p in pts ]).replace(', ',',')
    text = Text ( \
      'Spice_param:wg_length=%.3fu wg_width=%.3fu points="%s" radius=%s' %\
        (waveguide_length, self.width, pts_txt,self.radius ), t, 0.1*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
    t = Trans(angle, False, pt4)
    text = Text ( \
      'Length=%.3fu' %(waveguide_length), t, 0.5*wg_width, -1  )
    text.halign=halign
    shape = self.cell.shapes(LayerDevRecN).insert(text)
"""
