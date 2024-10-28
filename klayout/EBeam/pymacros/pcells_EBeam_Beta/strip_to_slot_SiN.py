import pya
from SiEPIC.utils import get_technology_by_name
from pya import *


class strip_to_slot_SiN(pya.PCellDeclarationHelper):
    """
    Simple strip to sloted taper for the SiN plaform
    draft by Bobby Zou Oct 24, 2024
    """

    def __init__(self):
        super(strip_to_slot_SiN, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")
        
        # declare the parameters
        self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['SiN'])
        self.param("w", self.TypeDouble, "Waveguide Width", default=1)
        self.param("rails", self.TypeDouble, "Rails", default=0.5)
        self.param("slot", self.TypeDouble, "Slot", default=0.12)
        self.param("length", self.TypeDouble, "Length", default=100)
        self.param("interfaceGap", self.TypeDouble, "Interface Slot Gap", default = 0.3)

        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "Strip_to_Slot_SiN(rails="
            + ("%.3f" % self.rails)
            + ",slot="
            + ("%g" % (self.slot))
            + ")"
            + ",width="
            + ("%g" % self.w)
        )
    
    def can_create_from_shape_impl(self):   
        return False
    

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from SiEPIC.extend import to_itype
        from SiEPIC.utils import arc_wg_xy

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        cell = self.cell
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Use to_itype() to prevent rounding errors
        w = to_itype(self.w, dbu)
        rails = to_itype(self.rails, dbu)
        slot = to_itype(self.slot, dbu)
        length = to_itype(self.length, dbu)
        interfaceGap = to_itype(self.interfaceGap, dbu)

        # Create the strip to top 1/2 waveguide
        pts = []
        pts.append(Point.from_dpoint(DPoint(0, -w/2)))
        pts.append(Point.from_dpoint(DPoint(0, w/2)))
        pts.append(Point.from_dpoint(DPoint(length, slot/2 + rails)))
        pts.append(Point.from_dpoint(DPoint(length, slot/2)))
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)

        # Create the bottom 1/2 waveguide
        pts = []
        pts.append(Point.from_dpoint(DPoint(0, -w/2 - interfaceGap - 0.12 /dbu)))
        pts.append(Point.from_dpoint(DPoint(0, -w/2 - interfaceGap)))
        pts.append(Point.from_dpoint(DPoint(length, -slot/2)))
        pts.append(Point.from_dpoint(DPoint(length, -slot/2 - rails)))
        
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)

        # PinRec Left
        shapes(LayerPinRecN).insert(
            pya.Path(
                [
                    pya.Point(0.05 / dbu, 0),
                    pya.Point(-0.05 / dbu, 0),
                ],
                w,
            )
        )
        shapes(LayerPinRecN).insert(
            pya.Text("opt1", pya.Trans(pya.Trans.R0, 0, 0))
        ).text_size = 0.5 / dbu

        # PinRec Right
        shapes(LayerPinRecN).insert(
            pya.Path(
                [
                    pya.Point(length-0.05 / dbu, 0),
                    pya.Point(length+0.05 / dbu, 0),
                ],
                2 * rails + slot,
            )
        )
        shapes(LayerPinRecN).insert(
            pya.Text("opt2", pya.Trans(pya.Trans.R0, length, 0))
        ).text_size = 0.5 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        dev = pts = []
        pts.append(Point.from_dpoint(DPoint(0, -w/2 - interfaceGap - 0.12 /dbu - w)))
        pts.append(Point.from_dpoint(DPoint(0, w/2 + w)))
        pts.append(Point.from_dpoint(DPoint(length, slot/2 + rails + w)))
        pts.append(Point.from_dpoint(DPoint(length, -slot/2 - rails - w)))
        polygon = Polygon(pts)
        shapes(LayerDevRecN).insert(polygon)