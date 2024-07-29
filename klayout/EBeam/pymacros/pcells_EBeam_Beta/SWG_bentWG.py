import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class SWG_bentWG(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(SWG_bentWG, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("pitch", self.TypeDouble, "Period [um]", default=0.2)
        self.param("w", self.TypeDouble, "Waveguide Width [um]", default=0.5)
        self.param(
            "r", self.TypeDouble, "Radius [um]", default=5
        )  # minimum radius is 5 um in TE
        self.param("ff", self.TypeDouble, "Duty Cycle", default=0.5)
        self.param("angle", self.TypeDouble, "Angle", default=360)
        self.param("gap", self.TypeDouble, "Bus Gap [um]", default=0.06)
        self.param("W_ratio", self.TypeDouble, "Lin/Lout", default=1)
        self.param(
            "doublebus",
            self.TypeBoolean,
            "Bus Type (Single=False, Double=True)",
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
        return "SWG_bentWG_%.3f" % (self.pitch)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        debug = False

        from SiEPIC.extend import to_itype
        import math
        from pya import DPolygon
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
        W_ratio = self.W_ratio
        doublebus = self.doublebus
        if debug:
            print(doublebus)

        # set the deltaL of sT-shaped silicon pillar (deltaL = (Lin-Lout)/4)
        deltaL = (2 * pitch * ff) * (W_ratio - 1) / ((1 + W_ratio) * (4))

        if r - w / 2 <= 0:
            r = 5
            if debug:
                print("invalid radius, set r to default: 5")

        # Calculate number of segments
        s1 = pitch * ff  # silicon
        s2 = pitch - s1  # gap

        # calculate best radius
        pi = math.pi
        const = math.ceil(2 * pi * r / (s1 + s2))
        # if doesn't divide evenly, replace r with best possible r
        if (2 * pi * r) % (s1 + s2) != 0:
            r = const * (s1 + s2) / (2 * pi)
            if debug:
                print("r adjusted to " + str(r) + "um to fit periods perfectly.")

        # theta1 = (s1/r)
        # theta2 = (s2/r)
        theta1 = math.atan(s1 / r)  # angle of silicon compared to the origin point
        theta2 = math.atan(s2 / r)  # angle of the gap compared to the origin point
        nSeg = int(
            math.floor(angle / (math.degrees(theta1) + math.degrees(theta2)))
        )  # how many segments to have
        si_first = True  # for alternating between silicon and gap
        j = 0  # index of how many silicon thetas
        jj = 0  # index of how many gap thetas
        ORDER = True  # ordering of the coordinates for polygon drawing

        # xo = [(r-w/2)*math.cos(0)]
        # yo = [(r-w/2)*math.sin(0)]
        # xo.append((r+w/2)*math.cos(0))
        # yo.append((r+w/2)*math.sin(0))

        xo = [(r - w / 2) * math.cos(0) + deltaL * math.sin(0)]
        yo = [(r - w / 2) * math.sin(0) - deltaL * math.cos(0)]
        xo.append((r + w / 2) * math.cos(0) - deltaL * math.sin(0))
        yo.append((r + w / 2) * math.sin(0) + deltaL * math.cos(0))

        for i in range(0, nSeg * 2):
            if si_first:
                j = j + 1
                si_first = not (si_first)
            else:
                jj = jj + 1
                si_first = not (si_first)

            if ORDER:
                xo.append(
                    (r + w / 2) * math.cos(j * theta1 + jj * theta2)
                    + deltaL * math.sin(j * theta1 + jj * theta2)
                )
                yo.append(
                    (r + w / 2) * math.sin(j * theta1 + jj * theta2)
                    - deltaL * math.cos(j * theta1 + jj * theta2)
                )
                xo.append(
                    (r - w / 2) * math.cos(j * theta1 + jj * theta2)
                    - deltaL * math.sin(j * theta1 + jj * theta2)
                )
                yo.append(
                    (r - w / 2) * math.sin(j * theta1 + jj * theta2)
                    + deltaL * math.cos(j * theta1 + jj * theta2)
                )
                ORDER = not (ORDER)
            else:
                xo.append(
                    (r - w / 2) * math.cos(j * theta1 + jj * theta2)
                    + deltaL * math.sin(j * theta1 + jj * theta2)
                )
                yo.append(
                    (r - w / 2) * math.sin(j * theta1 + jj * theta2)
                    - deltaL * math.cos(j * theta1 + jj * theta2)
                )
                xo.append(
                    (r + w / 2) * math.cos(j * theta1 + jj * theta2)
                    - deltaL * math.sin(j * theta1 + jj * theta2)
                )
                yo.append(
                    (r + w / 2) * math.sin(j * theta1 + jj * theta2)
                    + deltaL * math.cos(j * theta1 + jj * theta2)
                )
                ORDER = not (ORDER)

            if len(xo) == 4:
                dpts = [pya.DPoint(xo[i], yo[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)
                xo = []
                yo = []

        # Draw Bus WG
        # calulate ideal length of bus
        bus_length = self.cell.bbox().height() * dbu + pitch * 2
        constant = math.ceil(bus_length / (s1 + s2))
        if bus_length % (s1 + s2) != 0:
            bus_length = constant * (s1 + s2)

        # draw first box at center
        xo = [
            (r + w / 2 + gap),
            (r + w / 2 + gap + w),
            (r + w / 2 + gap + w),
            (r + w / 2 + gap),
        ]
        yo = [0, 0, s1, s1]
        dpts = [pya.DPoint(xo[i], yo[i]) for i in range(len(xo))]
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)

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

        if doublebus:
            for i in range(0, int(math.ceil((constant) / 2))):
                x2 = [xo[j] * -1 for j in range(len(xo))]
                yu = [yo[j] + i * pitch for j in range(len(yo))]
                yd = [yo[j] - i * pitch for j in range(len(yo))]

                dpts = [pya.DPoint(x2[i], yu[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)
                dpts = [pya.DPoint(x2[i], yd[i]) for i in range(len(xo))]
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
                shapes(LayerSiN).insert(element)

        # DEV BOX
        if doublebus is False:
            half_l = (self.cell.bbox().width() - w / dbu - gap / dbu) / 2
            half_r = self.cell.bbox().width() - half_l
            dev = Box(-half_l, yd[-4] / dbu, half_r, yu[-1] / dbu)
            shapes(LayerDevRecN).insert(dev)
            dev_width = self.cell.bbox().width() / 2
        else:
            half_l = (self.cell.bbox().width()) / 2
            half_r = self.cell.bbox().width() - half_l
            dev = Box(-half_l, yd[-4] / dbu, half_r, yu[-1] / dbu)
            shapes(LayerDevRecN).insert(dev)
            dev_width = self.cell.bbox().width() / 2

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.w, dbu)
        gap = to_itype(self.gap, dbu)
        bus_length = to_itype(bus_length / 2, dbu)

        # Pin1
        t = Trans(Trans.R0, half_r - w / 2, yu[-1] / dbu)
        pin = Path([Point(0, -pin_length / 2), Point(0, pin_length / 2)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin2
        t = Trans(Trans.R0, half_r - w / 2, yd[-4] / dbu)
        pin = Path([Point(0, pin_length / 2), Point(0, -pin_length / 2)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        if doublebus is True:
            half_l = self.cell.bbox().width() / 2
            half_r = self.cell.bbox().width() - half_l
            # pin 3
            t = Trans(Trans.R0, -half_l + w / 2, yu[-1] / dbu)
            pin = Path([Point(0, -pin_length / 2), Point(0, pin_length / 2)], w)
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = Text("pin3", t)
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.4 / dbu

            # Pin4
            t = Trans(Trans.R0, -half_l + w / 2, yd[-4] / dbu)
            pin = Path([Point(0, pin_length / 2), Point(0, -pin_length / 2)], w)
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = Text("pin4", t)
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.4 / dbu
