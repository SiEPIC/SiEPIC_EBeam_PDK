import pya
from SiEPIC.utils import get_technology_by_name
from pya import *


class strip_to_slot(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip_to_slot.
    draft by Lukas Chrostowski july 24, 2017
    Modified by Alexander Tofini march 17, 2021
    based on https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-21-16-19029&id=259920

    updated by Lukas Chrostowski, 2021/12
      - reduce the curved waveguide section, longer device for lower loss
      - simulated using EME to give 99% efficiency
    """

    def __init__(self):
        super(strip_to_slot, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")
        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r", self.TypeDouble, "Radius", default=15)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("rails", self.TypeDouble, "Rails", default=0.25)
        self.param("slot", self.TypeDouble, "Slot", default=0.1)
        self.param("taper", self.TypeDouble, "Taper Length", default=15.0)
        self.param("wt", self.TypeDouble, "Terminated Curved Width", default=0.1)
        self.param(
            "offset", self.TypeDouble, "Ending Offset for Curved section", default=1.0
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "Strip_To_Slot(rails="
            + ("%.3f" % self.rails)
            + ",slot="
            + ("%g" % (self.slot))
            + ")"
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

        LayerSi = self.silayer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Use to_itype() to prevent rounding errors
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)
        slot = to_itype(self.slot, dbu)
        rails = to_itype(self.rails, dbu)
        taper = to_itype(self.taper, dbu)
        # draw the quarter-circle
        x = 0
        y = r + rails / 2 + w + slot

        t = Trans(Trans.R0, x, y)
        # self.cell.shapes(LayerSiN).insert(Path(arc(r, 270, 360), rails).transformed(t).simple_polygon())
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x, y, r, rails, 270, 360))

        pts = []
        pts.append(Point.from_dpoint(DPoint(0, w)))
        pts.append(Point.from_dpoint(DPoint(0, 0)))
        pts.append(Point.from_dpoint(DPoint(-taper, w - rails)))
        pts.append(Point.from_dpoint(DPoint(-taper, w)))
        polygon = Polygon(pts)
        shapes(LayerSiN).insert(polygon)

        # Create the top left 1/2 waveguide
        wg1 = Box(-taper, w + slot, 0, w + rails + slot)
        shapes(LayerSiN).insert(wg1)

        from SiEPIC.utils import arc_wg_xy

        # Create the waveguide
        wg1 = Box(0, 0, r + w, w)
        shapes(LayerSiN).insert(wg1)

        # Pin on the slot waveguide side:
        shapes(LayerPinRecN).insert(
            pya.Path(
                [
                    pya.Point(-taper + 0.05 / dbu, w + slot / 2),
                    pya.Point(-taper - 0.05 / dbu, w + slot / 2),
                ],
                2 * rails + slot,
            )
        )
        shapes(LayerPinRecN).insert(
            pya.Text("opt1", pya.Trans(pya.Trans.R0, -taper, w))
        ).text_size = 0.5 / dbu

        # Pin on the bus waveguide side:
        shapes(LayerPinRecN).insert(
            pya.Path(
                [
                    pya.Point(r + w - 0.05 / dbu, w / 2),
                    pya.Point(r + w + 0.05 / dbu, w / 2),
                ],
                w,
            )
        )
        shapes(LayerPinRecN).insert(
            pya.Text("opt2", pya.Trans(pya.Trans.R0, r + w, w / 2))
        ).text_size = 0.5 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        dev = Box(-taper, -w / 2 - w, r + w, y)
        shapes(LayerDevRecN).insert(dev)
