import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils.layout import make_pin


class SWG_Ring(pya.PCellDeclarationHelper):
    """
    Author: Ben Cohen (UBC), Kithmin Wickremasinghe (UBC)
    Date: 2024-07-22
    This Pcell creates a sub-wavelengh grating (SWG) ring resonator

    Parameters:
      pitch  - grating period [um]
      w      - waveguide width [um]
      r      - ring radii [um]
      ff     - grating duty cycle (%)
      angle  - angle of the resonator (360 = full ring)
      gap2   - coupling gap [um]
      busL   - bus waveguide length [um]
      taperL - SWG <-> Strip Taper
    """

    def __init__(self):
        # Important: initialize the super class
        super(SWG_Ring, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("pitch", self.TypeDouble, "Period [um]", default=0.25)
        self.param("w", self.TypeDouble, "Waveguide Width [um]", default=0.5)
        self.param(
            "r", self.TypeDouble, "Radius [um]", default=30
        )  # minimum radius is 5 um in TE
        self.param("ff", self.TypeDouble, "Duty Cycle", default=0.5)
        self.param("angle", self.TypeDouble, "Angle", default=360)
        self.param("gap2", self.TypeDouble, "Bus Gap [um]", default=0.06)
        self.param("busL", self.TypeDouble, "Bus Length [um]", default=100)
        self.param("taperL", self.TypeDouble, "Taper Length [um]", default=30)

        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param(
            "oxideopen",
            self.TypeLayer,
            "Oxide Open Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "SWG_multibox_%.3f" % (self.pitch)

    def produce_impl(self):
        debug = False
        from SiEPIC.extend import to_itype
        import math
        from pya import DPolygon

        pi = math.pi

        ###################### Instantiations + Checking

        # Fetch the Parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Instantiate the Pcell Parameters
        pitch = self.pitch  # SWG Period [um]
        w = self.w  # Waveguide Width [um]
        r = self.r  # Ring Radii [um]
        ff = self.ff  # SWG Duty Cycle [%]
        angle = self.angle  # Angle of the ring
        gap2 = self.gap2  # Coupling Gap [um]
        busL = self.busL  # Bus Length [um]
        taperL = self.taperL  # Taper Length [um]

        # Minimize Ring Radii to 5 um
        if r - w / 2 <= 0:
            r = 5
            if debug:
                print("invalid radius, set r to default: 5")

        # Bus waveguide should be longer than 2x*taperL + 10 um for coupling
        if busL <= 10:
            busL = taperL * 2 + 10
            if debug:
                print(
                    "invalid length of SWG bus waveguide, set length at least 2 times larger than taper length and plus 10 um"
                )

        # Calculate number of SWG segments within the resonator
        s1 = pitch * ff  # silicon
        s2 = pitch - s1  # gap

        # draw oxide open
        shapes(ly.layer(self.oxideopen)).insert(
            pya.Box(
                DPoint(-to_itype(r + 5, dbu), -to_itype(r + 5, dbu)),
                DPoint(to_itype(r + 5, dbu), to_itype(r + 5, dbu)),
            )
        )

        ###################### Draw the Multi-box Ring

        # Calculate a radius to fit all of the gratings
        const = math.floor(2 * pi * r / (s1 + s2))
        # if doesn't divide evenly, replace r with best possible r
        if (2 * pi * r) % (s1 + s2) != 0:
            r = const * (s1 + s2) / (2 * pi)
            if debug:
                print("r adjusted to " + str(r) + "um to fit periods perfectly.")

        # Draw the SWGs
        theta1 = math.atan(s1 / r)
        theta2 = math.atan(s2 / r)
        nSeg = int(
            math.floor(angle / (math.degrees(theta1) + math.degrees(theta2)))
        )  # NUmber of SWG segments

        si_first = True  # for alternating between silicon and gap
        j = 0  # Index of how many silicon thetas
        jj = 0  # Index of how many gap thetas
        ORDER = True  # Ordering of the coordinates for polygon drawing

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
        r = r - w

        # Draw the Bus Waveguides
        r = self.r  # to go back to the initial point for Multi-box drawing, ger the first adjusted r value
        const = math.floor(2 * pi * r / (s1 + s2))

        # If doesn't divide evenly, replace r with best possible r
        if (2 * pi * r) % (s1 + s2) != 0:
            r = const * (s1 + s2) / (2 * pi)

        # calulate ideal length of bus
        bus_length = busL
        constant = math.ceil(bus_length / (s1 + s2))
        if bus_length % (s1 + s2) != 0:
            bus_length = constant * (s1 + s2)

        xo = [
            (r + w / 2 + gap2),
            (r + w / 2 + gap2 + w),
            (r + w / 2 + gap2 + w),
            (r + w / 2 + gap2),
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
            ((r + w / 2 + gap2) + (w - 0.06) / 2),
            ((r + w / 2 + gap2) + (w - 0.06) / 2 + 0.06),
            ((r + w / 2 + gap2) + w),
            (r + w / 2 + gap2),
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

        # Bus Strip Waveguide
        xTu = [min(xtu), min(xtu), min(xtu) + w, min(xtu) + w]

        yTu = [max(ytu), round(max(ytu) + busL), round(max(ytu) + busL), max(ytu)]

        dpts = [pya.DPoint(xTu[i], yTu[i]) for i in range(len(xtu))]
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)

        yTd = [min(ytd), round(min(ytd) - busL), round(min(ytd) - busL), min(ytd)]

        dpts = [pya.DPoint(xTu[i], yTd[i]) for i in range(len(xtu))]
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1.0 / dbu))
        shapes(LayerSiN).insert(element)

        # DEV BOX
        half_l = (self.cell.bbox().width() - (w) / dbu - gap2 / dbu) / 2
        half_r = self.cell.bbox().width() - half_l
        dev = Box(-half_l, max(yTu) / dbu, half_r, min(yTd) / dbu)
        shapes(LayerDevRecN).insert(dev)
        dev_width = self.cell.bbox().width() / 2

        # Create the pins on the waveguides, as short paths:

        bus_length = to_itype(bus_length / 2, dbu)

        # Pin1
        x_pin = max(xTu) - w / 2
        y_pin = max(yTu)
        make_pin(self.cell, "opt1", [x_pin, y_pin], w, LayerPinRecN, 90)

        # t = DTrans(Trans.R0, (max(xTu) - w/2)/dbu, max(yTu)/dbu)
        # pin = Path([Point(0, -pin_length/2), Point(0, pin_length/2)], 500) #500 is width of std WG
        # pin_t = pin.transformed(t)
        # shapes(LayerPinRecN).insert(pin_t)
        # text = Text ("opt1", t)
        # shape = shapes(LayerPinRecN).insert(text)
        # shape.text_size = 0.4/dbu

        # Pin2
        x_pin = max(xTu) - w / 2
        y_pin = min(yTd)
        make_pin(self.cell, "opt2", [x_pin, y_pin], w, LayerPinRecN, 270)

        # t = DTrans(Trans.R0, (max(xTu) - w/2)/dbu, min(yTd)/dbu)
        # pin = Path([Point(0, pin_length/2), Point(0, -pin_length/2)], 500) #500 is width of std WG
        # pin_t = pin.transformed(t)
        # shapes(LayerPinRecN).insert(pin_t)
        # text = Text ("opt2", t)
        # shape = shapes(LayerPinRecN).insert(text)
        # shape.text_size = 0.4/dbu
