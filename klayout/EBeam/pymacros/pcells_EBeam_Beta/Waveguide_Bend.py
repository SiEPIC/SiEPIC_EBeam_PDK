from pya import *
import pya


class Waveguide_Bend(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the waveguide bend.
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_Bend, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("radius", self.TypeDouble, "Radius", default=10)
        self.param("wg_width", self.TypeDouble, "Waveguide Width", default=0.5)
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
        return "Waveguide_Bend(R=" + ("%.3f" % self.radius) + ")"

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

        # cell: layout cell to place the layout
        # LayerSiN: which layer to use
        # r: radius
        # w: waveguide width
        # length units in dbu

        from SiEPIC.utils import arc, arc_to_waveguide

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.silayer
        LayerSiN = self.silayer_layer
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        w = int(round(self.wg_width / dbu))
        r = int(round(self.radius / dbu))

        # draw the quarter-circle
        x = -r
        y = r
        # layout_arc_wg_dbu(self.cell, LayerSiN, x, y, r, w, 270, 360)
        t = Trans(Trans.R0, x, y)
        from SiEPIC import __version__

        if __version__ > "0.5.0":
            self.cell.shapes(LayerSiN).insert(
                arc_to_waveguide(arc(r, 270, 360, dbu=dbu), w).transformed(t)
            )
        else:
            self.cell.shapes(LayerSiN).insert(
                arc_to_waveguide(arc(r, 270, 360), w).transformed(t)
            )

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        # Pin on the top side:
        p2 = [Point(0, y - pin_length / 2), Point(0, y + pin_length / 2)]
        p2c = Point(0, y)
        self.set_p2 = p2c
        self.p2 = p2c
        pin = Path(p2, w)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, 0, y)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Pin on the left side:
        p1 = [Point(pin_length / 2 + x, 0), Point(-pin_length / 2 + x, 0)]
        p1c = Point(x, 0)
        self.set_p1 = p1c
        self.p1 = p1c
        pin = Path(p1, w)
        shapes(LayerPinRecN).insert(pin)
        t = Trans(Trans.R0, x, 0)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        t = Trans(Trans.R0, x, y)
        if __version__ > "0.5.0":
            self.cell.shapes(LayerDevRecN).insert(
                arc_to_waveguide(arc(r, 270, 360, dbu=dbu), w * 3).transformed(t)
            )
        else:
            self.cell.shapes(LayerDevRecN).insert(
                arc_to_waveguide(arc(r, 270, 360), w * 3).transformed(t)
            )
        # layout_arc_wg_dbu(self.cell, LayerDevRecN, x, y, r, w*3, 270, 360)

        # Compact model information
        t = Trans(Trans.R0, x + r / 10, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/EBeam", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r / 100
        t = Trans(Trans.R0, x + r / 10, r / 4)
        text = Text("Component=ebeam_bend_1550", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r / 100
        t = Trans(Trans.R0, x + r / 10, r / 2)
        text = Text(
            "Spice_param:radius=%.3fu wg_width=%.3fu" % (self.radius, self.wg_width), t
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = r / 100
