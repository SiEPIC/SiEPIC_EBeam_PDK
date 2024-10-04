"""
This file is part of the SiEPIC-EBeam-PDK

Version history:

Lukas Chrostowski 2023/02/19
 - PCell takes an input of the waveguide type from a dropdown list
    Loaded from Waveguides.xml
 - Metal heater
"""

from pya import *
import pya


class wg_heater(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(wg_heater, self).__init__()

        from SiEPIC.utils import get_technology_by_name, load_Waveguides_by_Tech

        """
    # https://github.com/KLayout/klayout/issues/879
    tech = self.layout.library().technology
    if not tech:
       tech = 'EBeam'
    self.technology_name = tech
    """
        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Load all waveguides
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)

        # declare the parameters

        default_wg = "SiN Strip TE 895 nm, w=450 nm"
        p = self.param(
            "waveguide_type", self.TypeList, "Waveguide Type", default=default_wg
        )
        #    p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default = self.waveguide_types[0]['name'])

        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])
        self.param("length", self.TypeDouble, "Length", default=100)
        self.param(
            "path",
            self.TypeShape,
            "Path",
            default=DPath([DPoint(0, 0), DPoint(100, 0)], 0.5),
            hidden=True,
        )

        self.param("mh_width", self.TypeInt, "Heater width (microns)", default=4)
        self.param(
            "mhlayer", self.TypeLayer, "Heater Layer", default=TECHNOLOGY["M1_heater"]
        )
        self.param(
            "mllayer",
            self.TypeLayer,
            "Metal contact layer",
            default=TECHNOLOGY["M2_router"],
        )
        self.param("metal_width", self.TypeDouble, "Metal contact width", default=10)

        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param(
            "pinrecm",
            self.TypeLayer,
            "PinRecM Layer (metal)",
            default=TECHNOLOGY["PinRecM"],
        )

        self.cellName = "wg_heater"

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s" % (self.cellName, self.length)

    def coerce_parameters_impl(self):
        self.path = DPath([DPoint(0, 0), DPoint(self.length, 0)], 0.5)
        # print(self.waveguide_type)

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

        from SiEPIC.extend import to_itype
        from SiEPIC.utils.layout import make_pin

        dbu = self.layout.dbu

        # Draw the waveguide geometry, new function in SiEPIC-Tools v0.3.90
        from SiEPIC.utils.layout import layout_waveguide4

        self.waveguide_length = layout_waveguide4(
            self.cell, self.path, self.waveguide_type, debug=False
        )

        # fetch design layers
        LayermlN = self.layout.layer(self.mllayer)
        LayermhN = self.layout.layer(self.mhlayer)
        LayerPinRecN = self.layout.layer(self.pinrec)
        LayerDevRecN = self.layout.layer(self.devrec)
        LayerPinRecM = self.layout.layer(self.pinrecm)

        # draw metal heater
        path = DPath([DPoint(0, 0), DPoint(self.length, 0)], self.mh_width)
        self.cell.shapes(LayermhN).insert(path.simple_polygon())

        # metal contact
        self.cell.shapes(LayermlN).insert(
            pya.DPath(
                [
                    pya.DPoint(self.metal_width / 2, -self.mh_width / 2),
                    pya.DPoint(self.metal_width / 2, self.mh_width / 2),
                ],
                self.metal_width,
            )
        )
        self.cell.shapes(LayermlN).insert(
            pya.DPath(
                [
                    pya.DPoint(self.length - self.metal_width / 2, -self.mh_width / 2),
                    pya.DPoint(self.length - self.metal_width / 2, self.mh_width / 2),
                ],
                self.metal_width,
            )
        )

        # metal pins
        mh_width = to_itype(self.mh_width, dbu)
        ml_width = to_itype(self.metal_width, dbu)
        make_pin(
            self.cell,
            "elec1",
            [self.metal_width / 2, self.mh_width / 2],
            ml_width,
            LayerPinRecM,
            90,
        )
        make_pin(
            self.cell,
            "elec2",
            [self.length - self.metal_width / 2, self.mh_width / 2],
            ml_width,
            LayerPinRecM,
            90,
        )

        # print("EBeam.%s: length %.3f um, complete" % (self.cellName, self.waveguide_length))
