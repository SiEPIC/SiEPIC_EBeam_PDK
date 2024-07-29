import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class SWG_MultiBox_Ring(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(SWG_MultiBox_Ring, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("pitch", self.TypeDouble, "Period [um]", default=0.24)
        self.param("w", self.TypeDouble, "Waveguide Width [um]", default=0.18)
        self.param(
            "r", self.TypeDouble, "Radius [um]", default=35
        )  # minimum radius is 5 um in TE
        self.param("ff", self.TypeDouble, "Duty Cycle", default=0.75)
        self.param("angle", self.TypeDouble, "Angle", default=360)
        self.param("gap", self.TypeDouble, "Row Gap [um]", default=0.06)
        self.param("gap2", self.TypeDouble, "Bus Gap [um]", default=0.06)
        self.param("row", self.TypeDouble, "Number of Rows", default=5)
        self.param("busL", self.TypeDouble, "Bus Length [um]", default=10)
        self.param("taperL", self.TypeDouble, "Taper Length [um]", default=25)
        # self.param("doublebus", self.TypeBoolean, "Bus Type (Single=False, Double=True)", default = False)
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        #    self.param("textl", self.TypeLayer, "Text Layer", default = LayerInfo(10, 0))
        self.param(
            "oxideopen",
            self.TypeLayer,
            "Oxide Open Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SWG_multibox_%.3f" % (self.pitch)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        debug = False
        from SiEPIC.extend import to_itype
        import math
        from pya import DPolygon

        pi = math.pi
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
        r = self.r
        ff = self.ff
        angle = self.angle
        gap = self.gap
        gap2 = self.gap2
        row = self.row
        busL = self.busL
        taperL = self.taperL
        # doublebus = self.doublebus
        # print(doublebus)

        if r - w / 2 <= 0:
            r = 5
            if debug:
                print("invalid radius, set r to default: 5")
        if row <= 1:
            row = 1
            if debug:
                print("invalid number of rows, set row to default: 1")
        if busL <= 10:
            busL = taperL * 2 + 10
            if debug:
                print(
                    "invalid length of SWG bus waveguide, set length at least 2 times larger than taper length and pluse 10 um"
                )
        # Calculate number of segments
        s1 = pitch * ff  # silicon
        s2 = pitch - s1  # gap

        # draw oxide open
        shapes(ly.layer(self.oxideopen)).insert(
            pya.Box(
                DPoint(-to_itype(r + 5, dbu), -to_itype(r + 5, dbu)),
                DPoint(to_itype(r + 5, dbu), to_itype(r + 5, dbu)),
            )
        )

        # Draw the Multi-box Ring
        for i in range(0, int(row)):  # draw different radius SWG rings
            # calculate best radius
            # const = math.ceil(2*pi*r/(s1+s2))
            const = math.floor(2 * pi * r / (s1 + s2))
            # if doesn't divide evenly, replace r with best possible r
            if (2 * pi * r) % (s1 + s2) != 0:
                r = const * (s1 + s2) / (2 * pi)
                if debug:
                    print("r adjusted to " + str(r) + "um to fit periods perfectly.")

            theta1 = math.atan(s1 / r)
            theta2 = math.atan(s2 / r)
            nSeg = int(
                math.floor(angle / (math.degrees(theta1) + math.degrees(theta2)))
            )  # how many segments to have
            si_first = True  # for alternating between silicon and gap
            j = 0  # index of how many silicon thetas
            jj = 0  # index of how many gap thetas
            ORDER = True  # ordering of the coordinates for polygon drawing

            xo = [(r - w / 2) * math.cos(0)]
            yo = [(r - w / 2) * math.sin(0)]
            xo.append((r + w / 2) * math.cos(0))
            yo.append((r + w / 2) * math.sin(0))

            for i in range(0, nSeg * 2):
                if si_first:
                    j = j + 1
                    si_first = not (si_first)
                else:
                    jj = jj + 1
                    si_first = not (si_first)

                if ORDER:
                    xo.append((r + w / 2) * math.cos(j * theta1 + jj * theta2))
                    yo.append((r + w / 2) * math.sin(j * theta1 + jj * theta2))
                    xo.append((r - w / 2) * math.cos(j * theta1 + jj * theta2))
                    yo.append((r - w / 2) * math.sin(j * theta1 + jj * theta2))
                    ORDER = not (ORDER)
                else:
                    xo.append((r - w / 2) * math.cos(j * theta1 + jj * theta2))
                    yo.append((r - w / 2) * math.sin(j * theta1 + jj * theta2))
                    xo.append((r + w / 2) * math.cos(j * theta1 + jj * theta2))
                    yo.append((r + w / 2) * math.sin(j * theta1 + jj * theta2))
                    ORDER = not (ORDER)

                if len(xo) == 4:
                    dpts = [pya.DPoint(xo[i], yo[i]) for i in range(len(xo))]
                    dpolygon = DPolygon(dpts)
                    element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                    shapes(LayerSiN).insert(element)
                    xo = []
                    yo = []
            r = r - (w + gap)
        # Draw the Bus Waveguides
        # Draw Bus WG
        # to go back to the initial point for Multi-box drawing, ger the first adjusted r value
        r = self.r
        const = math.floor(2 * pi * r / (s1 + s2))
        # if doesn't divide evenly, replace r with best possible r
        if (2 * pi * r) % (s1 + s2) != 0:
            r = const * (s1 + s2) / (2 * pi)

        # calulate ideal length of bus
        bus_length = busL
        # bus_length = self.cell.bbox().height()*dbu +pitch*2
        constant = math.ceil(bus_length / (s1 + s2))
        if bus_length % (s1 + s2) != 0:
            bus_length = constant * (s1 + s2)

        for ii in range(0, int(row)):
            xo = [
                (r + w / 2 + gap2 + ii * (w + gap)),
                (r + w / 2 + gap2 + w + ii * (w + gap)),
                (r + w / 2 + gap2 + w + ii * (w + gap)),
                (r + w / 2 + gap2 + ii * (w + gap)),
            ]
            yo = [0, 0, s1, s1]
            dpts = [pya.DPoint(xo[i], yo[i]) for i in range(len(xo))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)

            # draw the bus waveguide
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
            xtu = [
                ((r + w / 2 + gap2 + ii * (w + gap)) + (w - 0.06) / 2),
                ((r + w / 2 + gap2 + ii * (w + gap)) + (w - 0.06) / 2 + 0.06),
                ((r + w / 2 + gap2 + ii * (w + gap)) + w + gap / 2),
                ((r + w / 2 + gap2 + ii * (w + gap)) - gap / 2),
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
            (r + w / 2 + gap2 - gap / 2),
            (r + w / 2 + gap2 - gap / 2 + row * (gap + w)),
            (r + w / 2 + gap2 + row * (gap + w) / 2 + 0.25),
            (r + w / 2 + gap2 + row * (gap + w) / 2 - 0.25),
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

        # add std WG
        if 2 * r >= busL + 2 * taperL:
            xstdu = [
                (r + w / 2 + gap2 + row * (gap + w) / 2 - 0.25),
                (r + w / 2 + gap2 + row * (gap + w) / 2 + 0.25),
                (r + w / 2 + gap2 + row * (gap + w) / 2 + 0.25),
                (r + w / 2 + gap2 + row * (gap + w) / 2 - 0.25),
            ]
            ystdu = [
                (yu[3] + taperL),
                (yu[3] + taperL),
                (yu[3] + r - busL / 2 + 1),
                (yu[3] + r - busL / 2 + 1),
            ]
            dpts = [pya.DPoint(xstdu[i], ystdu[i]) for i in range(len(xstdu))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)

            ystdd = [
                (yd[1] - taperL),
                (yd[1] - taperL),
                (yd[1] - r + busL / 2 - 1),
                (yd[1] - r + busL / 2 - 1),
            ]
            dpts = [pya.DPoint(xstdu[i], ystdd[i]) for i in range(len(xstdu))]
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
            shapes(LayerSiN).insert(element)
        else:
            xstdu = xTu
            ystdu = yTu
            ystdd = yTd

        # DEV BOX
        half_l = (
            self.cell.bbox().width()
            - row * (gap + w) / dbu
            - gap2 / dbu
            + (gap / 2) / dbu
        ) / 2
        half_r = self.cell.bbox().width() - half_l
        dev = Box(-half_l, ystdd[-1] / dbu - 1, half_r, ystdu[-1] / dbu + 1)
        shapes(LayerDevRecN).insert(dev)
        dev_width = self.cell.bbox().width() / 2

        if 2 * r >= busL + 2 * taperL:
            dev_up = (
                yu[-1] / dbu
                + taperL / dbu
                + (yu[3] + r - busL / 2 + 1 - (yu[3] + taperL)) / dbu
            )
            dev_down = (
                yd[-4] / dbu
                - taperL / dbu
                - (yu[3] + r - busL / 2 + 1 - (yu[3] + taperL)) / dbu
            )
        else:
            dev_up = yu[-1] / dbu + taperL / dbu
            dev_down = yd[-4] / dbu - taperL / dbu

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.w, dbu)
        gap = to_itype(self.gap, dbu)
        bus_length = to_itype(bus_length / 2, dbu)

        # Pin1
        # t = Trans(Trans.R0, dev_width-w/2,dev_up)
        t = Trans(Trans.R0, xstdu[-1] / dbu + 251, dev_up + 1)
        pin = Path(
            [Point(0, -pin_length / 2), Point(0, pin_length / 2)], 500
        )  # 500 is width of std WG
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("opt1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        if debug:
            print(dev_up)
            print(dev_up * dbu)
        # Pin2
        t = Trans(Trans.R0, xstdu[-1] / dbu + 251, dev_down - 1)
        pin = Path([Point(0, pin_length / 2), Point(0, -pin_length / 2)], 500)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("opt2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
