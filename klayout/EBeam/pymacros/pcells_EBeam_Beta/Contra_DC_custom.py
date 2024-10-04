import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Contra_DC_custom(pya.PCellDeclarationHelper):
    """
    Author:   Mustafa Hammood
              Mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Contra_DC_custom, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "number_of_periods1", self.TypeInt, "Number of grating periods", default=300
        )
        self.param(
            "grating_period1", self.TypeDouble, "Grating period (inner)", default=0.318
        )
        self.param(
            "grating_period2", self.TypeDouble, "Grating period (outer)", default=0.318
        )
        self.param("gap", self.TypeDouble, "Gap (microns)", default=0.15)
        self.param(
            "corrugation_width1outer",
            self.TypeDouble,
            "Waveguide 1 Corrugration width (outer)",
            default=0.03,
        )
        self.param(
            "corrugation_width1inner",
            self.TypeDouble,
            "Waveguide 1 Corrugration width (inner)",
            default=0.04,
        )
        self.param(
            "corrugation_width2outer",
            self.TypeDouble,
            "Waveguide 2 Corrugration width (inner)",
            default=0.01,
        )
        self.param(
            "corrugation_width2inner",
            self.TypeDouble,
            "Waveguide 2 Corrugration width (outer)",
            default=0.01,
        )
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.45)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.55)
        self.param("index", self.TypeDouble, "Gaussian Index", default=2.8)
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Contra_DC_dualBragg%s-%.3f" % (
            self.number_of_periods1,
            self.grating_period1,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        import math

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from SiEPIC.extend import to_itype

        # Draw the Bragg grating (bottom):
        width_period1 = to_itype(self.grating_period1 / 2, dbu)
        width_period2 = to_itype(self.grating_period2 / 2, dbu)

        grating_period1 = to_itype(self.grating_period1, dbu)
        grating_period2 = to_itype(self.grating_period2, dbu)

        w1 = to_itype(self.wg1_width, dbu)
        w2 = to_itype(self.wg2_width, dbu)

        GaussianIndex = self.index

        N1 = self.number_of_periods1

        vertical_offset1 = to_itype(self.gap / 2 + self.wg1_width / 2, dbu)
        vertical_offset2 = to_itype(-self.gap / 2 - self.wg2_width / 2, dbu)

        for i in range(0, self.number_of_periods1):
            x1 = to_itype(i * self.grating_period1, dbu)
            x2 = to_itype(i * self.grating_period2, dbu)

            profileFunction = math.exp(
                -0.5 * (2 * GaussianIndex * (i - N1 / 2) / (N1)) ** 2
            )

            profile_outer = (
                to_itype(self.corrugation_width1outer, dbu) * profileFunction
            )
            profile_inner = (
                to_itype(self.corrugation_width1inner, dbu) * profileFunction
            )

            box1outer = Box(
                x1,
                vertical_offset1 + w1 / 2 - profile_outer / 2,
                x1 + width_period1,
                vertical_offset1,
            )
            box2outer = Box(
                x1 + width_period1,
                vertical_offset1 + w1 / 2 + profile_outer / 2,
                x1 + 2 * width_period1,
                vertical_offset1,
            )

            box1inner = Box(
                x2,
                vertical_offset1 - w1 / 2 - profile_inner / 2,
                x2 + width_period2,
                vertical_offset1,
            )
            box2inner = Box(
                x2 + width_period2,
                vertical_offset1 - w1 / 2 + profile_inner / 2,
                x2 + 2 * width_period2,
                vertical_offset1,
            )

            shapes(LayerSiN).insert(box1outer)
            shapes(LayerSiN).insert(box2outer)

            shapes(LayerSiN).insert(box1inner)
            shapes(LayerSiN).insert(box2inner)

            length1 = x1 + grating_period1
            length2 = x2 + grating_period2

        if grating_period1 > grating_period2:
            box_inner = Box(
                length2, vertical_offset1, length1, vertical_offset1 - w1 / 2
            )
            shapes(LayerSiN).insert(box_inner)
            length = x1 + grating_period1
        else:
            box_outer = Box(
                length1, vertical_offset1, length2, vertical_offset1 + w1 / 2
            )
            shapes(LayerSiN).insert(box_outer)
            length = x2 + grating_period2

        # lower waveguide
        for i in range(0, self.number_of_periods1):
            x1 = to_itype(i * self.grating_period1, dbu)
            x2 = to_itype(i * self.grating_period2, dbu)

            profileFunction = math.exp(
                -0.5 * (2 * GaussianIndex * (i - N1 / 2) / (N1)) ** 2
            )

            profile_outer = (
                to_itype(self.corrugation_width2outer, dbu) * profileFunction
            )
            profile_inner = (
                to_itype(self.corrugation_width2inner, dbu) * profileFunction
            )

            box1outer = Box(
                x2,
                vertical_offset2 + w2 / 2 + profile_outer / 2,
                x2 + width_period2,
                vertical_offset2,
            )
            box2outer = Box(
                x2 + width_period2,
                vertical_offset2 + w2 / 2 - profile_outer / 2,
                x2 + 2 * width_period2,
                vertical_offset2,
            )

            box1inner = Box(
                x1,
                vertical_offset2 - w2 / 2 + profile_inner / 2,
                x1 + width_period1,
                vertical_offset2,
            )
            box2inner = Box(
                x1 + width_period1,
                vertical_offset2 - w2 / 2 - profile_inner / 2,
                x1 + 2 * width_period1,
                vertical_offset2,
            )

            shapes(LayerSiN).insert(box1outer)
            shapes(LayerSiN).insert(box2outer)

            shapes(LayerSiN).insert(box1inner)
            shapes(LayerSiN).insert(box2inner)

            length1 = x1 + grating_period1
            length2 = x2 + grating_period2

        if grating_period1 > grating_period2:
            box_inner = Box(
                length2, vertical_offset2, length1, vertical_offset2 + w2 / 2
            )
            shapes(LayerSiN).insert(box_inner)
            length = x1 + grating_period1
        else:
            box_outer = Box(
                length1, vertical_offset2, length2, vertical_offset2 - w2 / 2
            )
            shapes(LayerSiN).insert(box_outer)
            length = x2 + grating_period2

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.wg2_width, dbu)
        t = Trans(Trans.R0, 0, vertical_offset2)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, 0, vertical_offset1)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, length, vertical_offset1)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(Trans.R0, length, vertical_offset2)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 10, 0)
        text = Text("Component=ebeam_contra_dc", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 9, 0)
        text = Text("Spice_param:number_of_periods=%s" % (self.number_of_periods1), t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        t = Trans(Trans.R0, 0, 0)
        path = Path([Point(0, 0), Point(length, 0)], 3 * w)
        shapes(LayerDevRecN).insert(path.simple_polygon())
