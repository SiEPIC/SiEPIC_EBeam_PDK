import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Contra_DC_SWG(pya.PCellDeclarationHelper):
    """
    Author:   Mustafa Hammood
              Mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Contra_DC_SWG, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "number_of_periods", self.TypeInt, "Number of grating periods", default=300
        )
        self.param(
            "grating_period", self.TypeDouble, "Grating period (microns)", default=0.24
        )
        self.param("gap", self.TypeDouble, "Minimum gap (microns)", default=0.15)
        self.param(
            "corrugation_width1",
            self.TypeDouble,
            "Waveguide 1 Corrugration width (microns)",
            default=0.03,
        )
        self.param(
            "corrugation_width2",
            self.TypeDouble,
            "Waveguide 2 Corrugration width (microns)",
            default=0.04,
        )
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.45)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.55)
        self.param("duty", self.TypeDouble, "Duty cycle (0-1)", default=0.5)
        self.param("a", self.TypeDouble, "Gaussian Index", default=2.7)
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    #    self.param("textl", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Contra_DC_SWG%s-%.3f" % (self.number_of_periods, self.grating_period)

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

        N = self.number_of_periods
        grating_period = int(round(self.grating_period / dbu))
        misalignment = 0

        # Determine the period such that the waveguide length is as desired.  Slight adjustment to period
        N_boxes = N

        # Draw the Bragg grating:
        box_width = int(round(grating_period * self.duty))

        w1 = self.wg1_width / dbu
        half_w1 = w1 / 2
        w2 = self.wg2_width / dbu
        half_w2 = w2 / 2
        deltaW1_max = to_itype(self.corrugation_width1, dbu)
        deltaW2_max = to_itype(self.corrugation_width2, dbu)

        for i in range(0, N_boxes + 1):
            # apply apodization
            profileFunction = math.exp(-0.5 * (2 * self.a * (i - N / 2) / (N)) ** 2)
            deltaW1 = deltaW1_max * profileFunction
            deltaW2 = deltaW2_max * profileFunction

            vertical_offset = (
                int(round(self.wg2_width / 2 / dbu))
                + int(round(self.gap / dbu))
                + int(round(self.wg1_width / 2 / dbu))
            )  # +(-int(round(deltaW1))+int(round(deltaW2)))/2
            t = Trans(Trans.R0, 0, vertical_offset)

            if i % 2 == True:
                x = int(round((i * grating_period - box_width / 2)))
                box1_a = Box(x, -half_w1 - deltaW1, x + box_width, half_w1 - deltaW1)
                shapes(LayerSiN).insert(box1_a)

                box2_a = Box(
                    x + grating_period,
                    -half_w2 - deltaW2,
                    x + grating_period + box_width,
                    half_w2 - deltaW2,
                ).transformed(t)
                shapes(LayerSiN).insert(box2_a)

            else:
                x = int(round((i * grating_period - box_width / 2)))
                box1_b = Box(x, -half_w1, x + box_width, half_w1)
                shapes(LayerSiN).insert(box1_b)

                box2_b = Box(
                    x + grating_period,
                    -half_w2,
                    x + grating_period + box_width,
                    half_w2,
                ).transformed(t)
                shapes(LayerSiN).insert(box2_b)

        # missing periods due to misalignments
        box_final = Box(
            x + grating_period, -half_w1, x + grating_period + box_width, half_w1
        )
        shapes(LayerSiN).insert(box_final)
        box_final = Box(
            -box_width / 2, -half_w2 - deltaW2, box_width / 2, half_w2 - deltaW2
        ).transformed(t)
        shapes(LayerSiN).insert(box_final)

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, to_itype(-box_width / 2, dbu * 1000), -deltaW1 / 2)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(
            Trans.R0,
            to_itype(-box_width / 2, dbu * 1000),
            vertical_offset - deltaW2 / 2,
        )
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(
            Trans.R0,
            to_itype(x + grating_period + box_width, dbu * 1000),
            vertical_offset - deltaW2 / 2,
        )
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg1_width, dbu)
        t = Trans(
            Trans.R0, to_itype(x + grating_period + box_width, dbu * 1000), -deltaW1 / 2
        )
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
