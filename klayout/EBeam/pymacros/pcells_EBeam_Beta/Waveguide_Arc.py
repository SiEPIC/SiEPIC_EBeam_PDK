import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Waveguide_Arc(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the waveguide arc.

    Author: Mustafa Hammood     mustafa@siepic.com
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_Arc, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("radius", self.TypeDouble, "Radius", default=10)
        self.param("wg_width", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("start_angle", self.TypeDouble, "Start Angle", default=0)
        self.param("stop_angle", self.TypeDouble, "Stop Angle", default=45)
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
        return "Waveguide_Arc(R=" + ("%.3f" % self.radius) + ")"

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
        # start_angle: starting angle of the arc
        # stop_agnle: stopping angle of the arc
        # length units in dbu
        import math
        from SiEPIC.utils import arc_wg

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN = self.silayer_layer
        #    LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from SiEPIC.extend import to_itype

        w = to_itype(self.wg_width, dbu)
        r = to_itype(self.radius, dbu)
        start_angle = self.start_angle
        stop_angle = self.stop_angle

        if start_angle > stop_angle:
            start_angle = self.stop_angle
            stop_angle = self.start_angle

        deg_to_rad = math.pi / 180.0

        # draw the arc
        x = 0
        y = 0

        from SiEPIC._globals import PIN_LENGTH as pin_length

        self.cell.shapes(LayerSiN).insert(arc_wg(r, w, start_angle, stop_angle))
        # Create the pins, as short paths:

        # Pin on the right side:
        x = r * math.cos(start_angle * deg_to_rad)
        y = r * math.sin(start_angle * deg_to_rad)

        x_pin = math.cos((90 - start_angle) * deg_to_rad) * pin_length / 2
        y_pin = math.sin((90 - start_angle) * deg_to_rad) * pin_length / 2

        p2 = [Point(x - x_pin, y + y_pin), Point(x + x_pin, y - y_pin)]
        p2c = Point(x, y)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, y)
        text = Text("pin2", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the left side:
        x = round(r * math.cos(stop_angle * deg_to_rad))
        y = round(r * math.sin(stop_angle * deg_to_rad))

        x_pin = math.cos((90.0 - stop_angle) * deg_to_rad) * pin_length / 2
        y_pin = math.sin((90.0 - stop_angle) * deg_to_rad) * pin_length / 2

        p1 = [Point(x + x_pin, y - y_pin), Point(x - x_pin, y + y_pin)]
        p1c = Point(x, y)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w)
        self.cell.shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, y)
        text = Text("pin1", t)
        shape = self.cell.shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        x = 0
        y = 0
        # layout_arc_wg_dbu(self.cell, LayerDevRecN, x, y, r, w*3, start_angle, stop_angle)
        self.cell.shapes(LayerDevRecN).insert(arc_wg(r, w * 3, start_angle, stop_angle))
