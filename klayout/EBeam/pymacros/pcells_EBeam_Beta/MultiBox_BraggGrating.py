import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class MultiBox_BraggGrating(pya.PCellDeclarationHelper):
    """
    Reference:
    Enxiao Luan, Han Yun, Minglei Ma, Daniel M. Ratner, Karen C. Cheung, and Lukas Chrostowski,
    "Label-free biosensing with a multi-box sub-wavelength phase-shifted Bragg grating waveguide"
    Biomedical Optics Express Vol. 10, Issue 9, pp. 4825-4838 (2019)
    https://doi.org/10.1364/BOE.10.004825
    Multibox Bragg Grating
    By Enxiao Luan at UBC, 2020, with fix by Lukas Chrostowski
    """

    def __init__(self):
        # Important: initialize the super class
        super(MultiBox_BraggGrating, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("pitch", self.TypeDouble, "Period of SWG [um]", default=0.24)
        self.param("w", self.TypeDouble, "Waveguide Width [um]", default=0.18)
        self.param(
            "wc", self.TypeDouble, "Corrugation width [um]", default=0.1
        )  # minimum radius is 5 um in TE
        self.param("ff", self.TypeDouble, "Duty Cycle", default=0.75)
        # self.param("angle", self.TypeDouble, "Angle", default = 360)
        self.param("gap", self.TypeDouble, "Row Gap [um]", default=0.06)
        # self.param("gap2", self.TypeDouble, "Bus Gap [um]", default = 0.06)
        self.param("row", self.TypeDouble, "Number of Rows of main WG", default=3)
        self.param(
            "Length",
            self.TypeDouble,
            "Bragg Grating Length on Each side [um]",
            default=30,
        )
        self.param("taperL", self.TypeDouble, "Taper Length [um]", default=10)
        self.param(
            "phaseshifted",
            self.TypeBoolean,
            "Bragg Type (Uniform=False, Phase-shifted=True)",
            default=False,
        )
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
        return "MultiBox_BraggGrating_length%.3f um " % (2 * self.Length)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        from SiEPIC.extend import to_itype
        from pya import DPolygon
        import math
        # This is the main part of the implementation: create the layout

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # variables
        pitch = self.pitch
        w = self.w
        wc = self.wc
        ff = self.ff
        # angle = self.angle
        gap = self.gap
        # gap2 = self.gap2
        row = self.row
        Length = self.Length
        taperL = self.taperL
        phaseshifted = self.phaseshifted
        # print(doublebus)

        if Length <= 3 * pitch:
            Length = 3 * pitch
            print(
                "invalid length of MultiBox Bragg grating, set length at least 3 times larger than the period of multibox blocks"
            )

        s1 = pitch * ff  # silicon
        s2 = pitch - s1  # gap

        # Draw the first Multi-box Waveguides
        # calulate ideal length of bus
        Bragg_length = Length
        # bus_length = self.cell.bbox().height()*dbu +pitch*2
        constant = math.ceil(Bragg_length / (s1 + s2))
        if Bragg_length % (s1 + s2) != 0:
            Bragg_length = constant * (s1 + s2)

        for ii in range(0, int(row)):
            xo = [
                (ii * (w + gap)),
                (w + ii * (w + gap)),
                (w + ii * (w + gap)),
                (ii * (w + gap)),
            ]
            yo = [0, 0, s1, s1]
            dpts = [pya.DPoint(xo[i], yo[i]) for i in range(len(xo))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)

            # draw the SWG waveguide from the center one to +/- positions
            for i in range(0, int(math.ceil((constant) / 2))):
                yu = [yo[j] + i * pitch for j in range(len(yo))]
                yd = [yo[j] - i * pitch for j in range(len(yo))]

                dpts = [pya.DPoint(xo[i], yu[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)
                dpts = [pya.DPoint(xo[i], yd[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

            # draw the tapers from waveguide to SWG
            if taperL != 0:
                xtu = [
                    ((ii * (w + gap)) + (w - 0.06) / 2),
                    ((ii * (w + gap)) + (w - 0.06) / 2 + 0.06),
                    ((ii * (w + gap)) + w + gap / 2),
                    ((ii * (w + gap)) - gap / 2),
                ]
                ytu = [(yu[3] - taperL), (yu[3] - taperL), (yu[3]), (yu[3])]
                dpts = [pya.DPoint(xtu[i], ytu[i]) for i in range(len(xtu))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

                ytd = [(yd[1] + taperL), (yd[1] + taperL), (yd[1]), (yd[1])]
                dpts = [pya.DPoint(xtu[i], ytd[i]) for i in range(len(xtu))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

                # taper connections from multi-tapers to std WG
                xTu = [
                    (-gap / 2),
                    (-gap / 2 + row * (gap + w)),
                    ((row * (gap + w) - gap) / 2 + 0.25),
                    ((row * (gap + w) - gap) / 2 - 0.25),
                ]
                yTu = [(yu[3]), (yu[3]), (yu[3] + taperL), (yu[3] + taperL)]
                dpts = [pya.DPoint(xTu[i], yTu[i]) for i in range(len(xTu))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

                yTd = [(yd[1]), (yd[1]), (yd[1] - taperL), (yd[1] - taperL)]
                dpts = [pya.DPoint(xTu[i], yTd[i]) for i in range(len(xTu))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)
                # f is the factor to define the Dev starting point
                f = 1

            if taperL == 0:
                yTd = yd
                yTu = yu
                xTu = [0, 0, 0, 0]
                f = 0

        # draw the corrugations of the Bragg gratings
        constant_c = math.ceil((Bragg_length - taperL) / (s1 + s2))

        for iii in range(0, int(math.ceil(constant_c / 4))):
            yuc = [yo[j] + 2 * iii * pitch for j in range(len(yo))]
            ydc = [yo[j] - 2 * iii * pitch for j in range(len(yo))]
            xlc = [-wc - s2, -s2, -s2, -wc - s2]
            xrc = [row * pitch, row * pitch + wc, row * pitch + wc, row * pitch]

            dpts = [pya.DPoint(xlc[i], yuc[i]) for i in range(len(xo))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)

            dpts = [pya.DPoint(xrc[i], yuc[i]) for i in range(len(xo))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)

        if phaseshifted is False:
            for iii in range(0, int(math.ceil(constant_c / 4))):
                # yuc = [yo[j]+2*iii*pitch for j in range(len(yo))]
                ydc = [yo[j] - 2 * iii * pitch for j in range(len(yo))]
                # xlc = [-wc-s2, -s2, -s2,-wc-s2]
                # xrc = [row*pitch, row*pitch+wc, row*pitch+wc, row*pitch]

                dpts = [pya.DPoint(xlc[i], ydc[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

                dpts = [pya.DPoint(xrc[i], ydc[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

        if phaseshifted is True:
            for iii in range(0, int(math.ceil(constant_c / 4))):
                # yuc = [yo[j]+2*iii*pitch for j in range(len(yo))]
                yddc = [yo[j] - pitch - 2 * iii * pitch for j in range(len(yo))]

                dpts = [pya.DPoint(xlc[i], yddc[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

                dpts = [pya.DPoint(xrc[i], yddc[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

        # DEV BOX
        dev = Box(
            f * (-gap - wc - (2) * pitch) / dbu,
            yTd[-1] / dbu,
            (wc + (row + 2) * pitch) / dbu,
            yTu[-1] / dbu,
        )
        shapes(LayerDevRecN).insert(dev)
        dev_width = self.cell.bbox().width() / 2

        dev_up = yu[-1] / dbu + taperL / dbu
        dev_down = yd[-4] / dbu - taperL / dbu

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.w, dbu)
        gap = to_itype(self.gap, dbu)

        # Pin1
        t = Trans(Trans.R0, xTu[-1] / dbu + 250, dev_up)
        pin = Path(
            [Point(0, -pin_length / 2), Point(0, pin_length / 2)], 500
        )  # 500 is width of std WG
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        t = Trans(Trans.R270, xTu[-1] / dbu + 250, dev_up)
        text = Text("pin1", t)
        text.halign = 0
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin2
        t = Trans(Trans.R0, xTu[-1] / dbu + 250, dev_down)
        pin = Path([Point(0, pin_length / 2), Point(0, -pin_length / 2)], 500)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        t = Trans(Trans.R90, xTu[-1] / dbu + 250, dev_down)
        text = Text("pin2", t)
        text.halign = 0
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Ref
        t = Trans(Trans.R270, xTu[-1] / dbu + 250 + 0.5 / dbu, dev_up)
        text = Text("Ref: E. Luan, doi.org/10.1364/BOE.10.004825", t)
        text.halign = 0
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
