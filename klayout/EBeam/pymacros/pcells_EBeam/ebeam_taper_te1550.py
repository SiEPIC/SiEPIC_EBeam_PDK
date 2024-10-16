import pya
from pya import *


class ebeam_taper_te1550(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the strip waveguide taper.
    """

    def __init__(self):
        # Important: initialize the super class
        super(ebeam_taper_te1550, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param(
            "wg_width1",
            self.TypeDouble,
            "Waveguide Width1 (CML only supports 0.4, 0.5, 0.6)",
            default=0.5,
        )
        self.param(
            "wg_width2",
            self.TypeDouble,
            "Waveguide Width2 (CML only supports 1, 2, 3)",
            default=3,
        )
        self.param(
            "wg_length",
            self.TypeDouble,
            "Waveguide Length (CML only supports a range of 1-10)",
            default=50,
        )
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
        return (
            "ebeam_taper_te1550(R="
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

        from SiEPIC.extend import to_itype

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

        w1 = to_itype(self.wg_width1, dbu)
        w2 = to_itype(self.wg_width2, dbu)
        length = to_itype(self.wg_length, dbu)

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
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = to_itype(0.4, dbu)

        # Pin on the right side:
        p2 = [Point(length - pin_length / 2, 0), Point(length + pin_length / 2, 0)]
        p2c = Point(length, 0)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w2)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, length, 0)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = to_itype(0.4, dbu)
        shape.text_halign = 2

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        w_max = max([w1, w2])
        w_min = max([w1, w2])
        path = Path([Point(0, 0), Point(length, 0)], (w_max + w_min) * 2)
        shapes(LayerDevRecN).insert(path.simple_polygon())

        # Compact model information
        t = Trans(Trans.R0, w1 / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = length / 100
        t = Trans(Trans.R0, length / 10, w1 / 4)
        text = Text("Component=ebeam_taper_te1550", t)
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
            "ebeam_taper_te1550("
            + ("%.3f-%.3f-%.3f" % (self.wg_width1, self.wg_width2, self.wg_length))
            + ")"
        )
