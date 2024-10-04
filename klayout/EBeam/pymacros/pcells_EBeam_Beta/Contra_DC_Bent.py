import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Contra_DC_Bent(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the bent-CDC half ring resonator pcell

    Author: Mustafa Hammood     mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Contra_DC_Bent, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "silayer_gratings",
            self.TypeLayer,
            "Si Gratings Layer",
            default=TECHNOLOGY["Si"],
        )
        self.param("radius", self.TypeDouble, "Radius (um)", default=25)
        self.param("gap", self.TypeDouble, "Gap (um)", default=0.28)
        self.param("bus_width", self.TypeDouble, "Bus Width (um)", default=0.45)
        self.param("ring_width", self.TypeDouble, "Ring Width (um)", default=0.55)

        self.param("period", self.TypeDouble, "Gratings Period (nm)", default=318)
        self.param(
            "deltaWB", self.TypeDouble, "Bus Corrugation Width (um)", default=0.04
        )
        self.param(
            "deltaWR", self.TypeDouble, "Ring Corrugation Width (um)", default=0.05
        )
        self.param("gamma", self.TypeDouble, "N (number of corrugations)", default=135)

        self.param("busBend", self.TypeDouble, "Bus-to-straight bend raidus", default=5)

        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        # hidden parameters, can be used to query this component:
        self.param(
            "p1",
            self.TypeShape,
            "DPoint location of pin1",
            default=Point(-10000, 0),
            hidden=True,
            readonly=True,
        )
        self.param(
            "p2",
            self.TypeShape,
            "DPoint location of pin2",
            default=Point(0, 10000),
            hidden=True,
            readonly=True,
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Contra_DC_Bent_(R=" + ("%.3f" % self.radius) + ")"

    def produce(self, layout, layers, parameters, cell):
        """
        coerce parameters (make consistent)
        """
        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # r: radius
        # w: waveguide width
        # length units in dbu

        from math import pi, cos, sin
        from SiEPIC.utils import arc_wg_xy

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN_gratings = self.silayer_gratings_layer
        LayerSiN = self.silayer_layer
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from SiEPIC.extend import to_itype

        w_bus = to_itype(self.bus_width, dbu)
        w_ring = to_itype(self.ring_width, dbu)
        w = w_ring
        r = int(round(self.radius / dbu))
        gap = int(round(self.gap / dbu))
        period = self.period
        deltaWR = int(round(self.deltaWR / dbu))
        N = int(self.gamma)
        deltaWB = int(round(self.deltaWB / dbu))
        busBendR = int(round(self.busBend / dbu))

        # Center of everything
        x = 0
        y = 0

        # Angle of CDC portion, also bend angle!
        periodAngle = (180 / pi) * (period / 2) / (r + w_ring / 2 + gap / 2)

        # Bend angle
        bendAngle = (180 / pi) * (N * period / 2) / (r + w_ring / 2 + gap / 2)

        # Bend radius of bus
        rBus = r + gap + w_bus / 2 + w_ring / 2

        N_input = N
        # Normalized number of corrugations to periodAngle
        N = N * periodAngle * 2

        # Convention:   Set A is the CDC portion that is not offsetted, set B is offsetted by corrugation width

        # Ring CDCs (set A)
        ii = periodAngle * 2
        while ii < N + periodAngle * 1.5:
            self.cell.shapes(LayerSiN_gratings).insert(
                arc_wg_xy(
                    x,
                    y,
                    r - deltaWR / 2,
                    w_ring,
                    90 + bendAngle - ii,
                    90 + bendAngle - ii - periodAngle,
                )
            )
            ii = ii + periodAngle
            ii = ii + periodAngle

        # Ring CDCs (set B)
        ii = periodAngle
        while ii < N:
            self.cell.shapes(LayerSiN_gratings).insert(
                arc_wg_xy(
                    x,
                    y,
                    r + deltaWR / 2,
                    w_ring,
                    90 + bendAngle - ii,
                    90 + bendAngle - ii - periodAngle,
                )
            )
            ii = ii + periodAngle
            ii = ii + periodAngle

        # Bus CDCs (set A)
        ii = periodAngle
        while ii < N:
            self.cell.shapes(LayerSiN_gratings).insert(
                arc_wg_xy(
                    x,
                    y,
                    rBus - deltaWB / 2,
                    w_bus,
                    90 + bendAngle - ii,
                    90 + bendAngle - ii - periodAngle,
                )
            )
            ii = ii + periodAngle
            ii = ii + periodAngle

        # Bus CDCs (set B)
        ii = periodAngle * 2
        while ii < N + periodAngle * 1.5:
            self.cell.shapes(LayerSiN_gratings).insert(
                arc_wg_xy(
                    x,
                    y,
                    rBus + deltaWB / 2,
                    w_bus,
                    90 + bendAngle - ii,
                    90 + bendAngle - ii - periodAngle,
                )
            )
            ii = ii + periodAngle
            ii = ii + periodAngle

        # Ring non-CDC left
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x, y, r, w_ring, 180 - (90 - bendAngle), 180)
        )

        # Ring non-CDC right
        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x, y, r, w_ring, 0, 90 - bendAngle))

        bendAngleRad = (pi / 180) * bendAngle
        # Draw Bus non-CDC Waveguide
        y_center = rBus * cos(bendAngleRad) + busBendR * cos(bendAngleRad)
        x_center = rBus * sin(bendAngleRad) + busBendR * sin(bendAngleRad)

        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x_center, y_center, busBendR, w_bus, 270 - bendAngle, 270)
        )
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(-x_center, y_center, busBendR, w_bus, 270, 270 - bendAngle)
        )

        # Create the pins, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        # Pin on the right side:
        y_center = rBus * cos(bendAngleRad) + busBendR * cos(bendAngleRad) - busBendR
        p2 = [
            Point(-pin_length / 2 + x_center, y_center),
            Point(pin_length / 2 + x_center, y_center),
        ]
        p2c = Point(x_center, y_center)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w_bus)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x_center, y_center)
        text = Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the left side:
        x_center = -x_center
        p1 = [
            Point(pin_length / 2 + x_center, y_center),
            Point(-pin_length / 2 + x_center, y_center),
        ]
        p1c = Point(x_center, y_center)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w_bus)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x_center, y_center)
        text = Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the bottom left side:
        p3 = [Point(x - r, pin_length / 2 + y), Point(x - r, -pin_length / 2 + y)]
        p3c = Point(x - r, y)
        self.set_p3 = p3c
        self.p3 = p3c
        pin = Path(p3, w_ring)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x - r, y)
        text = Text("pin3", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the bottom right side:
        p4 = [Point(x + r, y + pin_length / 2), Point(x + r, y - pin_length / 2)]
        p4c = Point(x + r, y)
        self.set_p4 = p4c
        self.p4 = p4c
        pin = Path(p4, w_ring)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x + r, y)
        text = Text("pin4", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        self.cell.shapes(LayerDevRecN).insert(arc_wg_xy(x, y, r + gap, w * 5, 0, 180))
