from pya import *
import pya


class Waveguide_Straight(pya.PCellDeclarationHelper):
    """
    Input: length, width
    draws a straight waveguide with pins. centred at the instantiation point.
    Usage: instantiate, and use transformations (rotation)
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_Straight, self).__init__()
        from SiEPIC.utils import get_technology_by_name

        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("wg_length", self.TypeInt, "Waveguide Length", default=10000)
        self.param("wg_width", self.TypeInt, "Waveguide width", default=500)
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Waveguide_Straight_%.3f-%.3f" % (
            self.wg_length / 1000,
            self.wg_width / 1000,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        ly = self.layout
        LayerSiN = ly.layer(self.layer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        # LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        #    print("Waveguide_Straight:")
        w = self.wg_width
        length = self.wg_length
        points = [[-length / 2, 0], [length / 2, 0]]
        path = Path([Point(-length / 2, 0), Point(length / 2, 0)], w)
        #    print(path)

        shapes(LayerSiN).insert(path.simple_polygon())

        from SiEPIC._globals import PIN_LENGTH

        # Pins on the bus waveguide side:
        pin_length = PIN_LENGTH
        if length < pin_length + 1:
            pin_length = int(length / 3)
            pin_length = math.ceil(pin_length / 2.0) * 2
        if pin_length == 0:
            pin_length = 2

        t = Trans(Trans.R0, -length / 2, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = Trans(Trans.R0, length / 2, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/EBeam", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 10, 0)
        text = Text("Lumerical_INTERCONNECT_component=ebeam_wg_integral_1550", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 9, 0)
        text = Text(
            "Spice_param:wg_width=%.3fu wg_length=%.3fu"
            % (self.wg_width * dbu, self.wg_length * dbu),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        path = Path([Point(-length / 2, 0), Point(length / 2, 0)], w * 3)
        shapes(LayerDevRecN).insert(path.simple_polygon())
