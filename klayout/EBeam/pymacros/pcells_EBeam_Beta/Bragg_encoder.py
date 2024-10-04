import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Bragg_encoder(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(Bragg_encoder, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the paramters
        # parameters: binary code, start period, end period, corrugation width, length
        self.param("N", self.TypeDouble, "Number of bits (N)", default=8)
        self.param(
            "binary", self.TypeString, "identity (binary size N)", default="10000000"
        )
        self.param(
            "start_period", self.TypeDouble, "start period (microns)", default=0.314
        )
        self.param(
            "stop_period", self.TypeDouble, "stop period (microns)", default=0.342
        )
        self.param(
            "corrugation_widths",
            self.TypeList,
            "Corrugations widths (microns)",
            default=[0.08, 0.06, 0.04, 0.02, 0.02, 0.04, 0.06, 0.08],
        )
        self.param("wg_width", self.TypeDouble, "Waveguide width", default=0.50)
        self.param("length", self.TypeInt, "length (microns)", default=200)
        self.param("sum_format", self.TypeDouble, "sum format (1, 2, or 3)", default=3)

        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Bragg_encoder%s-%.3f-%.3f-%.3f" % (
            int(self.binary),
            self.start_period,
            self.stop_period,
            self.length,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    # function to create the device
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
        from math import pi, sin

        N = int(self.N)
        # draw the encoded bragg grating:
        dx = 0.01
        corrugations = self.corrugation_widths

        if N != len(self.binary):
            pya.MessageBox.warning(
                "Array length mismatch!",
                "Number of bits (N) does NOT equal the bits array length!",
                pya.MessageBox.Ok,
            )
            return
        elif N != len(self.corrugation_widths):
            pya.MessageBox.warning(
                "Array length mismatch!",
                "Number of bits (N) does NOT equal the corrugation widths array length!",
                pya.MessageBox.Ok,
            )
            return

        dlambda = (self.stop_period - self.start_period) / (N - 1)
        npoints = int(self.length / dx)
        w = to_itype(self.wg_width, dbu)
        l = to_itype(self.length, dbu)
        f = self.sum_format

        E = []
        wavelengths = []
        for i in range(0, N):
            E.append(int(self.binary[i]))
            wavelengths.append(self.start_period + i * dlambda)
            round(wavelengths[i], 3)

        x = 0
        y1 = 0
        y2 = 0
        pts1 = [Point(x, 0)]
        pts3 = [Point(x, 0)]
        for i in range(0, npoints + 1):
            x1 = i * dx

            # summation method
            if f == 1:
                for j in range(0, N):
                    corrugation = float(self.corrugation_widths[j]) / 10
                    y1 = y1 + corrugation * E[j] * sin((x1 * 2 * pi) / wavelengths[j])
                    y2 = y1

            elif f == 2:
                # half half method (11110000 style):
                for j in range(0, int(N / 2)):
                    corrugation1 = float(self.corrugation_widths[j]) / 10
                    corrugation2 = float(self.corrugation_widths[j + int(N / 2)]) / 10
                    y1 = y1 + corrugation1 * E[j] * sin((x1 * 2 * pi) / wavelengths[j])
                    y2 = y2 + corrugation2 * E[j + int(N / 2)] * sin(
                        (x1 * 2 * pi) / wavelengths[j + int(N / 2)]
                    )

            elif f == 3:
                # half half method (10101010 style):
                for j in range(0, int(N / 2)):
                    idx1 = int(j * 2)
                    idx2 = int((j * 2 + 1))

                    corrugation1 = float(self.corrugation_widths[idx1]) / 10
                    corrugation2 = float(self.corrugation_widths[idx2]) / 10
                    y1 = y1 + corrugation1 * E[idx1] * sin(
                        (x1 * 2 * pi) / wavelengths[idx1]
                    )
                    y2 = y2 + corrugation2 * E[idx2] * sin(
                        (x1 * 2 * pi) / wavelengths[idx2]
                    )

            if self.N == 2:
                dw1 = float(self.corrugation_widths[0])
                dw2 = float(self.corrugation_widths[1])
            else:
                dw1 = 0
                dw2 = 0

            pts1.append(Point((x + x1) / dbu, ((self.wg_width - dw1) / 2 + y1) / dbu))
            pts3.append(Point((x + x1) / dbu, ((-self.wg_width + dw2) / 2 - y2) / dbu))

        pts1.append(Point((x + x1 + 20 * dx) / dbu, self.wg_width / 2 / dbu))
        pts3.append(Point((x + x1 + 20 * dx) / dbu, -self.wg_width / 2 / dbu))

        pts1.append(Point((x + x1 + 20 * dx) / dbu, 0))
        pts3.append(Point((x + x1 + 20 * dx) / dbu, 0))

        shapes(LayerSiN).insert(Polygon(pts1))
        shapes(LayerSiN).insert(Polygon(pts3))

        # create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        t = Trans(Trans.R0, 0, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = Trans(Trans.R0, (self.length + dx * 20) / dbu, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
