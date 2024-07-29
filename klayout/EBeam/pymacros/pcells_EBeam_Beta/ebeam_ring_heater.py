# This PCell instantiates two ebeam_dc_halfring_straight and adds a heater layer
# Mustafa Hammood, 2023

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_ring_heater(pya.PCellDeclarationHelper):
    """
    The PCell uses two ebeam_dc_halfring_straight PCells and adds a heater.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_ring_heater, self).__init__()
        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r", self.TypeDouble, "Radius", default=10)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("g", self.TypeDouble, "Gap", default=0.1)
        self.param("Lc", self.TypeDouble, "Coupler Length", default=0.0)
        self.param(
            "orthogonal_identifier",
            self.TypeInt,
            "Orthogonal identifier (1=TE, 2=TM)",
            default=1,
        )
        self.param("heater_width", self.TypeDouble, "Metal heater width", default=3)
        self.param("metal_width", self.TypeDouble, "Metal contact width", default=5)
        self.param(
            "l_heater", self.TypeLayer, "Heater Layer", default=TECHNOLOGY["M1_heater"]
        )
        self.param(
            "l_metal",
            self.TypeLayer,
            "Metal contact Layer",
            default=TECHNOLOGY["M2_router"],
        )
        self.param(
            "pinrecm",
            self.TypeLayer,
            "PinRecM Layer (metal)",
            default=TECHNOLOGY["PinRecM"],
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
            "ebeam_ring_heater(R="
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
        from SiEPIC.utils import arc
        from SiEPIC.extend import to_itype
        from SiEPIC.utils.layout import make_pin

        dbu = self.layout.dbu
        center = to_itype(self.r * 2 + self.g * 2 + self.w * 2, self.layout.dbu) / 2
        mh_layer = self.layout.layer(self.l_heater)
        ml_layer = self.layout.layer(self.l_metal)
        LayerPinRecM = self.layout.layer(self.pinrecm)
        m_radius = to_itype(self.r, dbu)
        mh_width = to_itype(self.heater_width, dbu)
        ml_width = to_itype(self.metal_width, dbu)

        # add heater
        poly = pya.Polygon(arc(m_radius + mh_width / 2, 0, 360))
        hole = pya.Polygon(arc(m_radius - mh_width / 2, 0, 360))
        poly.insert_hole(hole.get_points())
        self.cell.shapes(mh_layer).insert(
            poly.transform(pya.Trans(pya.Trans.R0, 0, center))
        )
        # add contacts
        m_length = to_itype(3, dbu)
        pts = [
            Point(m_radius, center - ml_width / 2),
            Point(m_radius, center + ml_width / 2),
            Point(m_radius + m_length, center + ml_width / 2),
            Point(m_radius + m_length, center - ml_width / 2),
        ]
        self.cell.shapes(ml_layer).insert(Polygon(pts))
        self.cell.shapes(mh_layer).insert(Polygon(pts))

        pts = [
            Point(-m_radius, center - ml_width / 2),
            Point(-m_radius, center + ml_width / 2),
            Point(-m_radius - m_length, center + ml_width / 2),
            Point(-m_radius - m_length, center - ml_width / 2),
        ]
        self.cell.shapes(ml_layer).insert(Polygon(pts))
        self.cell.shapes(mh_layer).insert(Polygon(pts))

        # add rings
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
        make_pin(
            self.cell, "elec1", [m_radius + m_length, center], ml_width, LayerPinRecM, 0
        )
        make_pin(
            self.cell,
            "elec2",
            [-m_radius - m_length, center],
            ml_width,
            LayerPinRecM,
            180,
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

        # print("Done drawing the layout for - ebeam_ring_heater: %.3f-%g" % ( self.r, self.g) )
