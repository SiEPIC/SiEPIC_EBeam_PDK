import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Contra_DC_SWG_segmented(pya.PCellDeclarationHelper):
    """
    Author:   Mustafa Hammood
              Mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Contra_DC_SWG_segmented, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "number_of_periods", self.TypeInt, "Number of grating periods", default=300
        )
        self.param(
            "grating_period",
            self.TypeDouble,
            "Sub-wavelength period (microns)",
            default=0.24,
        )
        self.param(
            "cdc_period",
            self.TypeDouble,
            "Pertrubation period (microns)",
            default=0.464,
        )
        self.param("gap", self.TypeDouble, "Minimum gap (microns)", default=0.1)
        self.param(
            "corrugation_width",
            self.TypeDouble,
            "Waveguide Corrugration width (microns)",
            default=0.12,
        )
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.5)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.38)
        self.param("duty", self.TypeDouble, "Duty cycle (0 to 1)", default=0.5)
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
        cdc_period = int(round(self.cdc_period / dbu))
        misalignment = 0

        # Determine the period such that the waveguide length is as desired.  Slight adjustment to period
        N_boxes = N

        # Draw the Bragg grating:
        box_width = int(round(grating_period * self.duty))

        w1 = self.wg1_width / dbu
        half_w1 = w1 / 2
        w2 = self.wg2_width / dbu
        half_w2 = w2 / 2
        w = self.corrugation_width / dbu
        half_w = w / 2
        gap = int(round(self.gap / dbu))

        vertical_offset = (
            int(round(self.wg2_width / 2 / dbu))
            + 2 * gap
            + int(round(self.wg1_width / 2 / dbu))
            + int(round(w))
        )

        t = Trans(Trans.R0, to_itype(0, dbu), vertical_offset)

        for i in range(0, N_boxes + 1):
            if i % 2 == True:
                x = int(round((i * grating_period - box_width / 2)))

                box1_a = Box(x, -half_w1, x + box_width, half_w1)
                shapes(LayerSiN).insert(box1_a)

                box2_a = Box(
                    x + grating_period,
                    -half_w2,
                    x + grating_period + box_width,
                    half_w2,
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

        # compensate length of SWG boxes vs cdc boxes
        x_cdc = int(round(N_boxes * cdc_period) / 2)
        xk = int(round(N_boxes * grating_period))
        N_cdc_boxes = 2 * int(round((xk - x_cdc) / cdc_period))
        # print(N_cdc_boxes)
        for i in range(0, N_boxes + 1 + N_cdc_boxes):
            if i % 2 == True:
                x_cdc = int(round((i * cdc_period / 2 - box_width / 2)))

                boxw_a = Box(
                    x_cdc,
                    -half_w1 - gap,
                    x_cdc + cdc_period / 2,
                    -w - half_w1 - gap,
                )
                shapes(LayerSiN).insert(boxw_a)

                boxw_a = Box(
                    x_cdc,
                    half_w2 + gap,
                    x_cdc + cdc_period / 2,
                    w + half_w2 + gap,
                ).transformed(t)
                shapes(LayerSiN).insert(boxw_a)

            else:
                x_cdc = int(round((i * cdc_period / 2 - box_width / 2)))
                boxw_a = Box(
                    x_cdc,
                    half_w1 + gap,
                    x_cdc + cdc_period / 2,
                    w + half_w1 + gap,
                )
                shapes(LayerSiN).insert(boxw_a)

        # missing periods due to misalignments
        box_final = Box(
            x + grating_period, -half_w1, x + grating_period + box_width, half_w1
        )
        shapes(LayerSiN).insert(box_final)
        box_final = Box(-box_width / 2, -half_w2, box_width / 2, half_w2).transformed(t)
        shapes(LayerSiN).insert(box_final)

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, to_itype(-box_width / 2, dbu * 1000), 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(Trans.R0, to_itype(-box_width / 2, dbu * 1000), vertical_offset)
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
            vertical_offset,
        )
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, to_itype(x + grating_period + box_width, dbu * 1000), 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin4", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
