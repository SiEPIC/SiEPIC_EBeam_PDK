# This PCell instantiates two ebeam_dc_halfring_straight

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ring_doublebus(pya.PCellDeclarationHelper):
    """
    The PCell uses two ebeam_dc_halfring_straight PCells.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ring_doublebus, self).__init__()
        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r", self.TypeDouble, "Radius", default=10)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("g", self.TypeDouble, "Gap", default=0.2)
        self.param("Lc", self.TypeDouble, "Coupler Length", default=0.0)
        self.param(
            "orthogonal_identifier",
            self.TypeInt,
            "Orthogonal identifier (1=TE, 2=TM)",
            default=1,
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "ring_doublebus(R="
            + ("%.3f" % self.r)
            + ",g="
            + ("%g" % (1000 * self.g))
            + ",Lc="
            + ("%g" % (1000 * self.Lc))
            + ",orthogonal_identifier="
            + ("%s" % self.orthogonal_identifier)
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):
        # This is the main part of the implementation: create the layout

        from SiEPIC.extend import to_itype

        # print(self.layout.technology_name)  # the technology is not assigned in a PCell, for some reason
        self.layout.technology_name = self.technology_name

        pcell = self.layout.create_cell(
            "ebeam_dc_halfring_straight",
            self.technology_name,
            {
                "silayer": self.silayer,
                "r": self.r,
                "w": self.w,
                "g": self.g,
                "Lc": self.Lc,
                "orthogonal_identifier": self.orthogonal_identifier,
                "pinrec": self.pinrec,
                "devrec": self.devrec,
                "textl": self.textl,
            },
        )

        if pcell == None:
            raise Exception(
                "problem! cannot create PCell from library: %s" % self.technology_name
            )
        inst = self.cell.insert(
            pya.CellInstArray(pcell.cell_index(), pya.Trans(pya.Trans.R0, 0, 0))
        )
        inst = self.cell.insert(
            pya.CellInstArray(
                pcell.cell_index(),
                pya.Trans(
                    pya.Trans.R180,
                    0,
                    to_itype(self.r * 2 + self.g * 2 + self.w * 2, self.layout.dbu),
                ),
            )
        )
        # print((self.r*2+self.g*2+self.w*2)/self.layout.dbu)
        # print("Done drawing the layout for - ring_doublebus: %.3f-%g" % ( self.r, self.g) )
