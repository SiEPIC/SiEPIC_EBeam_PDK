# This PCell instantiates one ebeam_dc_halfring_straight and one waveguide

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ring_singlebus(pya.PCellDeclarationHelper):
    """
    The PCell uses one ebeam_dc_halfring_straight PCell and one waveguide
    """

    def __init__(self):
        # Important: initialize the super class
        super(ring_singlebus, self).__init__()

        from SiEPIC.utils import load_Waveguides_by_Tech

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

        # Load all waveguides types
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)
        p = self.param(
            "waveguide_type",
            self.TypeList,
            "Waveguide Type",
            default=self.waveguide_types[0]["name"],
        )
        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "ring_singlebus(R="
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

        # print(self.layout.technology_name)  # the technology is not assigned in a PCell, for some reason
        self.layout.technology_name = self.technology_name

        # Create the PCell
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
        # Instantiate the PCell in the layout
        inst = self.cell.insert(
            pya.CellInstArray(pcell.cell_index(), pya.Trans(pya.Trans.R0, 0, 0))
        )

        path = pya.DPath(
            [
                pya.DPoint(-self.r, self.r + self.g + self.w),
                pya.DPoint(-self.r, self.r * 2 + self.g + self.w),
                pya.DPoint(self.r, self.r * 2 + self.g + self.w),
                pya.DPoint(self.r, self.r + self.g + self.w),
            ],
            0.5,
        )

        wg_pcell = self.layout.create_cell(
            "Waveguide",
            self.technology_name,
            {"waveguide_type": self.waveguide_type, "path": path},
        )
        if wg_pcell == None:
            raise Exception(
                "problem! cannot create Waveguide from library: %s"
                % self.technology_name
            )
        inst = self.cell.insert(
            pya.CellInstArray(wg_pcell.cell_index(), pya.Trans(pya.Trans.R0, 0, 0))
        )

        # print("Done drawing the layout for - ring_singlebus: %.3f-%g" % ( self.r, self.g) )
