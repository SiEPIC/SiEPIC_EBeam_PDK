import pya
from SiEPIC.utils import get_technology_by_name
from pya import *

class slot_SiN(pya.PCellDeclarationHelper):
    """
    Simple sloted waveguide for the SiN plaform
    draft by Bobby Zou Oct 24, 2024

    """

    def __init__(self):
        super(slot_SiN, self).__init__()
        TECHNOLOGY = get_technology_by_name('EBeam')

        # declare the parameters
        self.param("layer", self.TypeLayer, "Layer", default = TECHNOLOGY['SiN'])
        self.param("w", self.TypeDouble, "Waveguide Width", default=1)
        self.param("rails", self.TypeDouble, "Rails", default=0.5)
        self.param("slot", self.TypeDouble, "Slot", default=0.12)
        self.param("length", self.TypeDouble, "Length", default=50)

        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "Slot_SiN(rails="
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

        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Use to_itype() to prevent rounding errors
        w = to_itype(self.w, dbu)
        rails = to_itype(self.rails, dbu)
        slot = to_itype(self.slot, dbu)
        length = to_itype(self.length, dbu)

        # Create the top left 1/2 waveguide
        wg1 = Box(0, slot/2, length, rails + slot/2)
        shapes(LayerSiN).insert(wg1)

        wg2 = Box(0, -(slot/2), length, -(rails + slot/2))
        shapes(LayerSiN).insert(wg2)

        # PinRec Left
        shapes(LayerPinRecN).insert(
            pya.Path(
                [
                    pya.Point(0.05 / dbu, 0),
                    pya.Point(-0.05 / dbu, 0),
                ],
                2 * rails + slot,
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
        dev = Box(0,-(rails + slot/2 + w), length, (rails + slot/2 + w))
        shapes(LayerDevRecN).insert(dev)