import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class DirectionalCoupler_Bent(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the bent-coupled half ring resonator pcell

    Author: Mustafa Hammood     mustafa@ece.ubc.ca
    """

    def __init__(self):
        # Important: initialize the super class
        super(DirectionalCoupler_Bent, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("radius", self.TypeDouble, "Radius", default=10)
        self.param("bus_radius", self.TypeDouble, "Bus Radius", default=5)
        self.param("gap", self.TypeDouble, "Gap", default=0.2)
        self.param("bus_width", self.TypeDouble, "Bus Width", default=0.5)
        self.param("ring_width", self.TypeDouble, "Ring Width", default=0.5)
        self.param("bend_angle", self.TypeDouble, "Bend angle", default=45)
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
        return "Bent_Coupler(R=" + ("%.3f" % self.radius) + ")"

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
        import math
        from SiEPIC.utils import arc_wg_xy
        from SiEPIC._globals import PIN_LENGTH as pin_length
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN = self.silayer_layer
        #    LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        w_bus = to_itype(self.bus_width, dbu)
        w_ring = to_itype(self.ring_width, dbu)
        r = to_itype(self.radius, dbu)
        r_bus = to_itype(self.bus_radius, dbu)
        bend_angle = int(round(self.bend_angle))
        gap = to_itype(self.gap, dbu)

        # **********************
        # Draw the ring waveguide
        # **********************

        x = 0
        y = 0

        self.cell.shapes(LayerSiN).insert(arc_wg_xy(x, y, r, w_ring, 0, 180))

        # Create the pins, as short paths:

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
        self.cell.shapes(LayerDevRecN).insert(arc_wg_xy(x, y, r, w_ring * 3, 0, 180))

        # **********************
        # Draw the bus waveguide (figure out how to call the existing class maybe??)
        # **********************

        r_original = to_itype(self.radius, dbu)

        r = r + gap + w_ring / 2 + w_bus / 2

        # number of points per circle:
        # npoints = int(points_per_circle(r))
        # increment, in radians, for each point:
        # da = 2 * pi / npoints

        # draw the first arc
        x = round(
            -r * math.sin(bend_angle * math.pi / 180)
            - r_bus * math.sin(bend_angle * math.pi / 180)
        )
        y = round(
            r * math.cos(bend_angle * math.pi / 180)
            + r_bus * math.cos(bend_angle * math.pi / 180)
        )

        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x, y, r_bus, w_bus, 270, 270 + bend_angle)
        )

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        self.cell.shapes(LayerDevRecN).insert(
            arc_wg_xy(x, y, r_bus, w_bus * 3, 270, 270 + bend_angle)
        )

        # draw the second arc
        r = to_itype(self.radius, dbu)
        x = 0
        y = 0

        r = r + gap + w_ring / 2 + w_bus / 2
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x, y, r, w_bus, 90 - bend_angle, 90 + bend_angle)
        )

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        self.cell.shapes(LayerDevRecN).insert(
            arc_wg_xy(x, y, r, w_bus * 3, 90 - bend_angle, 90 + bend_angle)
        )

        # draw the third arc

        x = round(
            r * math.sin(bend_angle * math.pi / 180)
            + r_bus * math.sin(bend_angle * math.pi / 180)
        )
        y = round(
            r * math.cos(bend_angle * math.pi / 180)
            + r_bus * math.cos(bend_angle * math.pi / 180)
        )

        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x, y, r_bus, w_bus, 270 - bend_angle, 270)
        )

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        self.cell.shapes(LayerDevRecN).insert(
            arc_wg_xy(x, y, r_bus, w_bus * 3, 270 - bend_angle, 270)
        )

        r = to_itype(self.radius, dbu)
        r = r + gap + w_ring / 2 + w_bus / 2
        # Pin on the left side:
        x = round(
            -r * math.sin(bend_angle * math.pi / 180)
            - r_bus * math.sin(bend_angle * math.pi / 180)
        )
        y = round(
            r * math.cos(bend_angle * math.pi / 180)
            + r_bus * math.cos(bend_angle * math.pi / 180)
            - r_bus
        )

        p2 = [Point(x + pin_length / 2, y), Point(x - pin_length / 2, y)]
        p2c = Point(x, y)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w_bus)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, y)
        text = Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the right side:
        p1 = [Point(-x - pin_length / 2, y), Point(-x + pin_length / 2, y)]
        p1c = Point(x, -r)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w_bus)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, -x, y)
        text = Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
