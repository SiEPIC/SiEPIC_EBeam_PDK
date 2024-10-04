import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_taper(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip waveguide taper.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_taper, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # Button to launch separate window
        self.param(
            "documentation", self.TypeCallback, "Open documentation in web browser"
        )
        #    self.param("simulation", self.TypeCallback, "Launch simulation GUI")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("wg_width1", self.TypeDouble, "Waveguide Width1", default=0.5)
        self.param("wg_width2", self.TypeDouble, "Waveguide Width2", default=3)
        self.param("wg_length", self.TypeDouble, "Waveguide Length", default=10)
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

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            url = "https://github.com/SiEPIC/SiEPIC_EBeam_PDK/blob/master/Documentation/Taper/Summary_Taper.pdf"
            import webbrowser

            webbrowser.open_new(url)

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return (
            "ebeam_taper(R="
            + ("%.3f-%.3f-%.3f" % (self.wg_width1, self.wg_width2, self.wg_length))
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce(self, layout, layers, parameters, cell):
        """
        coerce parameters (make consistent)
        """
        self._layers = layers
        self.cell = cell
        self._param_values = parameters
        self.layout = layout
        shapes = self.cell.shapes

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # w: waveguide width
        # length units in dbu

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout

        LayerSi = self.silayer
        LayerSiN = self.silayer_layer
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        w1 = int(round(self.wg_width1 / dbu))
        w2 = int(round(self.wg_width2 / dbu))
        length = int(round(self.wg_length / dbu))

        pts = [
            Point(0, -w1 / 2),
            Point(0, w1 / 2),
            Point(length, w2 / 2),
            Point(length, -w2 / 2),
        ]
        shapes(LayerSiN).insert(Polygon(pts))

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        # Pin on the left side:
        p1 = [Point(pin_length / 2, 0), Point(-pin_length / 2, 0)]
        p1c = Point(0, 0)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w1)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, 0, 0)
        text = Text("opt1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the right side:
        p2 = [Point(length - pin_length / 2, 0), Point(length + pin_length / 2, 0)]
        p2c = Point(length, 0)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w2)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, length, 0)
        text = Text("opt2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        path = Path([Point(0, 0), Point(length, 0)], w2 + w1 * 2)
        shapes(LayerDevRecN).insert(path.simple_polygon())

        # Compact model information
        t = Trans(Trans.R0, w1 / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=None", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = Trans(Trans.R0, length / 10, w1 / 4)
        text = Text("Component=ebeam_taper", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = Trans(Trans.R0, length / 10, w1 / 2)
        text = Text(
            "Spice_param:wg_width1=%.3fu wg_width2=%.3fu wg_length=%.3fu"
            % (self.wg_width1, self.wg_width2, self.wg_length),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100

        return (
            "ebeam_taper("
            + ("%.3f-%.3f-%.3f" % (self.wg_width1, self.wg_width2, self.wg_length))
            + ")"
        )
