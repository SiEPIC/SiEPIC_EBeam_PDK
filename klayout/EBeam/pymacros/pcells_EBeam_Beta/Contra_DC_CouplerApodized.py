import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Contra_DC_CouplerApodized(pya.PCellDeclarationHelper):
    """
    Author:   Mustafa Hammood
              Mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Contra_DC_CouplerApodized, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "number_of_periods", self.TypeInt, "Number of grating periods", default=300
        )
        self.param(
            "grating_period", self.TypeDouble, "Grating period (microns)", default=0.317
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
        self.param("AR", self.TypeBoolean, "Anti-Reflection Coating", default=True)
        self.param(
            "sinusoidal",
            self.TypeBoolean,
            "Grating Type (Rectangular=False, Sinusoidal=True)",
            default=False,
        )
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.45)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.55)
        self.param("index", self.TypeDouble, "Gaussian Index", default=2.5)
        self.param("H", self.TypeDouble, "Apodization H constant (microns)", default=2)
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
        return "Contra_DC_%s-%.3f" % (self.number_of_periods, self.grating_period)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        import math
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Draw the Bragg grating (bottom):
        box_width = int(round(self.grating_period / 2 / dbu))
        grating_period = int(round(self.grating_period / dbu))
        w = to_itype(self.wg1_width, dbu)
        GaussianIndex = self.index
        half_w = w / 2
        half_corrugation_w = int(round(self.corrugation_width1 / 2 / dbu))

        if self.AR:
            misalignment = grating_period / 2
        else:
            misalignment = 0

        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                x = round((i * self.grating_period) / dbu)
                deltaW1 = int(round(self.corrugation_width1 / 2 / dbu))
                box1 = Box(x, 0, x + box_width, half_w + deltaW1)
                pts1 = [Point(x, 0)]
                pts3 = [Point(x + misalignment, 0)]
                for i1 in range(0, npoints_sin + 1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(deltaW1 * math.sin(x1))
                    x1 = round(x1 / 2 / math.pi * grating_period)
                    #          print("x: %s, y: %s" % (x1,y1))
                    pts1.append(Point(x + x1, half_w + y1))
                    pts3.append(Point(x + misalignment + x1, -half_w - y1))
                pts1.append(Point(x + grating_period, 0))
                pts3.append(Point(x + grating_period + misalignment, 0))
                shapes(LayerSiN).insert(Polygon(pts1))
                shapes(LayerSiN).insert(Polygon(pts3))
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, half_w)
                shapes(LayerSiN).insert(box2)
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, -half_w)
                shapes(LayerSiN).insert(box3)

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period) / dbu))

                deltaW1 = int(round(self.corrugation_width1 / 2 / dbu))
                box1 = Box(x, 0, x + box_width, half_w + deltaW1)
                box2 = Box(x + box_width, 0, x + grating_period, half_w - deltaW1)
                box3 = Box(
                    x + misalignment, 0, x + box_width + misalignment, -half_w - deltaW1
                )
                box4 = Box(
                    x + box_width + misalignment,
                    0,
                    x + grating_period + misalignment,
                    -half_w + deltaW1,
                )
                shapes(LayerSiN).insert(box1)
                shapes(LayerSiN).insert(box2)
                shapes(LayerSiN).insert(box3)
                shapes(LayerSiN).insert(box4)
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, half_w)
                shapes(LayerSiN).insert(box2)
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, -half_w)
                shapes(LayerSiN).insert(box3)

        vertical_offset = (
            int(round(self.wg2_width / 2 / dbu))
            + int(round(self.gap / dbu))
            + int(round(self.wg1_width / 2 / dbu))
        )

        if misalignment > 0:
            t = Trans(Trans.R0, 0, vertical_offset)
        else:
            t = Trans(Trans.R0, 0, vertical_offset)

        # Draw the Bragg grating (top):
        box_width = int(round(self.grating_period / 2 / dbu))
        grating_period = int(round(self.grating_period / dbu))
        w = to_itype(self.wg2_width, dbu)
        GaussianIndex = self.index
        half_w = w / 2
        half_corrugation_w = int(round(self.corrugation_width2 / 2 / dbu))

        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                periodGap = int(round(self.gap / dbu))
                vertical_offset = (
                    int(round(self.wg2_width / 2 / dbu))
                    + periodGap
                    + int(round(self.wg1_width / 2 / dbu))
                )
                if misalignment > 0:
                    t = Trans(Trans.R0, 0, vertical_offset)
                else:
                    t = Trans(Trans.R0, 0, vertical_offset)

                x = round((i * self.grating_period) / dbu)
                deltaW2 = int(round(self.corrugation_width2 / 2 / dbu))
                box1 = Box(x, 0, x + box_width, -half_w + deltaW2).transformed(t)
                pts1 = [Point(x, 0)]
                pts3 = [Point(x + misalignment, 0)]
                for i1 in range(0, npoints_sin + 1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(deltaW2 * math.sin(x1))
                    x1 = round(x1 / 2 / math.pi * grating_period)
                    #          print("x: %s, y: %s" % (x1,y1))
                    pts1.append(Point(x + x1, -half_w - y1))
                    pts3.append(Point(x + misalignment + x1, +half_w + y1))
                pts1.append(Point(x + grating_period, 0))
                pts3.append(Point(x + grating_period + misalignment, 0))
                shapes(LayerSiN).insert(Polygon(pts1).transformed(t))
                shapes(LayerSiN).insert(Polygon(pts3).transformed(t))
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes(LayerSiN).insert(box2)
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, half_w).transformed(t)
                shapes(LayerSiN).insert(box3)

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period) / dbu))

                periodGap = int(round(self.gap / dbu)) + 2 * int(
                    round(self.H / dbu)
                ) * (1 - math.exp((-self.index * (i - 0.5 * N) ** 2) / (N**2)))
                vertical_offset = (
                    int(round(self.wg2_width / 2 / dbu))
                    + periodGap
                    + int(round(self.wg1_width / 2 / dbu))
                )
                if misalignment > 0:
                    t = Trans(Trans.R0, 0, vertical_offset)
                else:
                    t = Trans(Trans.R0, 0, vertical_offset)

                deltaW2 = int(round(self.corrugation_width2 / 2 / dbu))
                box1 = Box(x, 0, x + box_width, -half_w - deltaW2).transformed(t)
                box2 = Box(
                    x + box_width, 0, x + grating_period, -half_w + deltaW2
                ).transformed(t)
                box3 = Box(
                    x + misalignment, 0, x + box_width + misalignment, half_w + deltaW2
                ).transformed(t)
                box4 = Box(
                    x + box_width + misalignment,
                    0,
                    x + grating_period + misalignment,
                    half_w - deltaW2,
                ).transformed(t)
                shapes(LayerSiN).insert(box1)
                shapes(LayerSiN).insert(box2)
                shapes(LayerSiN).insert(box3)
                shapes(LayerSiN).insert(box4)
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes(LayerSiN).insert(box2)
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, half_w).transformed(t)
                shapes(LayerSiN).insert(box3)

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, 0, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(Trans.R0, 0, vertical_offset)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin3", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg1_width, dbu)
        t = Trans(Trans.R0, length, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(self.wg2_width, dbu)
        t = Trans(Trans.R0, length, vertical_offset)
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
        text = Text(
            "Spice_param:number_of_periods=%s grating_period=%.3fu corrugation_width=%.3fu misalignment=%.3fu sinusoidal=%s"
            % (
                self.number_of_periods,
                self.grating_period,
                self.corrugation_width1,
                misalignment,
                int(self.sinusoidal),
            ),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        t = Trans(Trans.R0, 0, 0)
        path = Path(
            [Point(0, vertical_offset / 2), Point(length, vertical_offset / 2)], 3 * w
        )
        shapes(LayerDevRecN).insert(path.simple_polygon())
