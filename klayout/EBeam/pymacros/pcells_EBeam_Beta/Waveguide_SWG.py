import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Waveguide_SWG(pya.PCellDeclarationHelper):
    """
    Input: length, target_period, wg_width, width, duty
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_SWG, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("length", self.TypeDouble, "Waveguide length", default=10.0)
        self.param(
            "target_period", self.TypeDouble, "Target period (microns)", default=0.200
        )
        self.param("wg_width", self.TypeDouble, "Waveguide width", default=0.5)
        self.param("duty", self.TypeDouble, "Duty Cycle (0 to 1)", default=0.7)
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
        return "Waveguide_SWG_%s-%.3f-%.3f-%.3f" % (
            self.length,
            self.target_period,
            self.wg_width,
            self.duty,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        # LayerSiSPN = ly.layer(LayerSiSP)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Determine the period such that the waveguide length is as desired.  Slight adjustment to period
        N_boxes = int(round(self.length / self.target_period - 0.5))
        grating_period = self.length / (N_boxes) / dbu
        # print("N boxes: %s, grating_period: %s" % (N_boxes, grating_period) )

        # Draw the Bragg grating:
        box_width = int(round(grating_period * self.duty))

        w = self.wg_width / dbu
        half_w = w / 2
        for i in range(0, N_boxes + 1):
            x = int(round((i * grating_period - box_width / 2)))
            box1 = Box(x, -half_w, x + box_width, half_w)
            shapes(LayerSiN).insert(box1)
        #    i = i + 1
        #    x = int(round((i * grating_period)))
        #    box1 = Box(x, -half_w, x + box_width, half_w)
        #    shapes(LayerSiN).insert(box1)
        length = self.length / dbu

        # Pins on the waveguide:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        #    pin_length = box_width
        t = Trans(Trans.R0, 0, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = Trans(Trans.R0, length, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 10, 0)
        text = Text("Component=NO_MODEL_AVAILABLE", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 9, -box_width * 2)
        text = Text(
            "Spice_param:length=%.3fu target_period=%.3fu grating_period=%.3fu wg_width=%.3fu duty=%.3f "
            % (
                self.length,
                self.target_period,
                round(grating_period) * dbu,
                self.wg_width,
                self.duty,
            ),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = [pya.Point(0, 0), pya.Point(length, 0)]
        path = pya.Path(points, w)
        path = pya.Path(points, w * 3)
        shapes(LayerDevRecN).insert(path.simple_polygon())
