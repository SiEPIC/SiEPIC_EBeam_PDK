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

        default_wg = "Strip TE 1550 nm, w=500 nm"
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
            "wg_width",
            self.TypeDouble,
            "Waveguide width (microns)",
            default=0.5,
            readonly=True,
        )
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
        self.param("text", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

        self.cellName = "wg_heater"

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s" % (self.cellName, self.length)

    def coerce_parameters_impl(self):
        params = [t for t in self.waveguide_types if t["name"] == self.waveguide_type]
        if not params:
            raise Exception("Waveguides.XML not correctly configured")
        self.wg_width = float(params[0]["width"])

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

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")
        params = [t for t in self.waveguide_types if t["name"] == self.waveguide_type]
        layer = [wg["layer"] for wg in params[0]["component"]]
        try:
            layer.remove("DevRec")
        except:
            pass
        if not layer:
            raise Exception("Waveguides.XML not correctly configured")

        # fetch design layers
        LayermlN = self.layout.layer(self.mllayer)
        LayermhN = self.layout.layer(self.mhlayer)
        LayerPinRecN = self.layout.layer(self.pinrec)
        LayerDevRecN = self.layout.layer(self.devrec)
        LayerPinRecM = self.layout.layer(self.pinrecm)
        LayerWG = ly.layer(TECHNOLOGY[layer[0]])
        LayerTextN = ly.layer(self.text)

        from SiEPIC.extend import to_itype
        from SiEPIC.utils.layout import make_pin

        dbu = self.layout.dbu
        w = to_itype(self.wg_width, dbu)

        # Draw the waveguide geometry
        path = DPath([DPoint(0, 0), DPoint(self.length, 0)], self.wg_width)
        self.cell.shapes(LayerWG).insert(path.simple_polygon())

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

        # Create the pins on the waveguides
        make_pin(self.cell, "opt1", [0, 0], w, LayerPinRecN, 180)
        make_pin(self.cell, "opt2", [to_itype(self.length, dbu), 0], w, LayerPinRecN, 0)

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        cml = "EBeam"
        if cml:
            text = Text("Lumerical_INTERCONNECT_library=Design kits/%s" % cml, t)
            shape = shapes(LayerDevRecN).insert(text)
            shape.text_size = 0.1 / dbu
            t = Trans(Trans.R0, 0, w * 2)
        model = "wg_heater"
        if model:
            text = Text("Component=%s" % model, t)
            shape = shapes(LayerDevRecN).insert(text)
            shape.text_size = 0.1 / dbu
            t = Trans(Trans.R0, 0, -w * 2)
        text = Text("Spice_param:wg_length=%.3fu" % (self.length), t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        h = max(w * 3 * dbu, self.mh_width / 2)
        box1 = Box(0, -to_itype(h, dbu), to_itype(self.length, dbu), to_itype(h, dbu))
        shapes(LayerDevRecN).insert(box1)
