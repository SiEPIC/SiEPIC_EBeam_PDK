import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class BraggWaveguide_holes(pya.PCellDeclarationHelper):
    """

    Waveguide Bragg grating using holes

    """

    def __init__(self):
        # Important: initialize the super class
        super(BraggWaveguide_holes, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param(
            "number_of_periods", self.TypeInt, "Number of grating periods", default=10
        )
        self.param(
            "grating_period", self.TypeDouble, "Grating period (microns)", default=0.260
        )
        self.param("fill_factor", self.TypeDouble, "Grating fill factor", default=0.5)
        self.param(
            "hole_width", self.TypeDouble, "Corrugration width (microns)", default=0.07
        )
        self.param("wg_width", self.TypeDouble, "Waveguide width", default=0.35)
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
        return "BraggWaveguide_holes_%s-%.3f-%.3f-%.3f" % (
            self.number_of_periods,
            self.grating_period,
            self.hole_width,
            self.fill_factor,
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
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        from SiEPIC.extend import to_itype

        # Draw the Bragg grating:
        grating_period = to_itype(self.grating_period, dbu)
        w = to_itype(self.wg_width, dbu)
        hole_width = to_itype(self.hole_width, dbu)
        fill_factor = self.fill_factor

        for i in range(0, self.number_of_periods):
            x = i * grating_period
            box1 = Box(x, -w / 2, x + grating_period * (1 - fill_factor), w / 2)
            box2 = Box(
                x + grating_period * (1 - fill_factor),
                -hole_width / 2,
                x + grating_period,
                -w / 2,
            )
            box3 = Box(
                x + grating_period * (1 - fill_factor),
                hole_width / 2,
                x + grating_period,
                w / 2,
            )
            shapes(LayerSiN).insert(box1)
            shapes(LayerSiN).insert(box2)
            shapes(LayerSiN).insert(box3)
            length = x + grating_period

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        t = Trans(Trans.R0, 0, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("opt1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.3 / dbu

        t = Trans(Trans.R0, length, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("opt2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.3 / dbu
        shape.text_halign = 2

        # Compact model information
        t = Trans(Trans.R0, 0, 0)
        text = Text("Lumerical_INTERCONNECT_library=Design kits/ebeam", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 10, 0)
        text = Text("Component=ebeam_bragg_te1550", t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu
        t = Trans(Trans.R0, length / 9, 0)
        text = Text(
            "Spice_param:number_of_periods=%s grating_period=%.3g hole_width=%.3g fill_factor=%.3g"
            % (
                self.number_of_periods,
                self.grating_period * 1e-6,
                self.hole_width * 1e-6,
                self.fill_factor,
            ),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        t = Trans(Trans.R0, 0, 0)
        path = Path([Point(0, 0), Point(length, 0)], 3 * w)
        shapes(LayerDevRecN).insert(path.simple_polygon())

        # print('Done: BraggWaveguide_holes')
