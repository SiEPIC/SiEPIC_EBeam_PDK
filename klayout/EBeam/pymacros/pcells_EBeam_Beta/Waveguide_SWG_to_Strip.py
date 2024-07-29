import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Waveguide_SWG_to_Strip(pya.PCellDeclarationHelper):
    """
    Input: length, period_strip, period_swg, wg_width_strip, wg_width_swg, duty_strip, duty_swg
    continuously (linearly) variable period, width, duty along the length

    Updated by Lukas Chrostowski, Leanne Dias, Connor Mosquera 2020/05
    """

    def __init__(self):
        # Important: initialize the super class
        super(Waveguide_SWG_to_Strip, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("wavelength", self.TypeDouble, "Wavelength", default=1310)
        self.param("fishbone", self.TypeBoolean, "Fishbone", default=False)
        self.param("length", self.TypeDouble, "Waveguide length", default=10.0)
        self.param(
            "taper_fraction",
            self.TypeDouble,
            "Strip taper length fraction (0 to 1)",
            default=1,
        )
        self.param(
            "period_strip",
            self.TypeDouble,
            "SWG Period at strip end (microns)",
            default=0.200,
        )
        self.param(
            "period_swg",
            self.TypeDouble,
            "SWG Period at SWG end (microns)",
            default=0.200,
        )
        self.param(
            "wg_width_strip",
            self.TypeDouble,
            "Strip Waveguide width at the taper end (microns)",
            default=0.5,
        )
        #    self.param("wg_width_swg_taperend", self.TypeDouble, "Waveguide width at SWG taper end (microns)", default = 0.4)
        self.param(
            "wg_width_swg",
            self.TypeDouble,
            "SWG Waveguide at end (microns)",
            default=0.5,
        )
        self.param(
            "wg_width_taper",
            self.TypeDouble,
            "Nanotaper width at taper end (microns)",
            default=0.06,
        )
        self.param(
            "duty_strip",
            self.TypeDouble,
            "SWG duty cycle at strip end (0 to 1)",
            default=0.500,
        )
        self.param(
            "duty_swg",
            self.TypeDouble,
            "SWG duty cycle at SWG end (0 to 1)",
            default=0.700,
        )
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Waveguide_SWG_to_Strip_%s-%.3f-%.3f-%.3f" % (
            self.length,
            self.period_swg,
            self.wg_width_swg,
            self.duty_swg,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        debug = False
        # Layout and layers:
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerSiSPN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # fetch the PCell parameters, and calculate a few things
        from SiEPIC.extend import to_itype

        wg_width_swg = to_itype(self.wg_width_swg, dbu)
        wg_width_strip = to_itype(self.wg_width_strip, dbu)
        length = to_itype(self.length, dbu)
        w1 = to_itype(self.wg_width_taper, dbu)
        w2 = to_itype(self.wg_width_strip, dbu)

        # Determine the period such that the waveguide length is as desired.  Slight adjustment to period
        N_boxes = int(
            round(self.length / (self.period_swg + self.period_strip) * 2.0) - 0.5
        )
        grating_period = self.length / (N_boxes) / dbu
        if debug:
            print("N boxes: %s, grating_period: %s" % (N_boxes, grating_period))

        # taper length, minus last SWG block
        # taper_length = int(round(self.taper_fraction * self.length / dbu))
        taper_length = (N_boxes - 1) * grating_period

        # Find out what is the delta width required between
        # a) the SWG end and b) the SWG with nanotaper
        # Done by simulating the neff versus SWG waveguide width, with an without a 60 nm
        w = wg_width_swg
        if self.fishbone:
            dw = 0
        elif self.wavelength == 1310:
            dw = -3.3736e-5 * w * w + 0.0618752 * w + 3.88577
        else:
            dw = 0
        wg_width_swg_taperend = wg_width_swg - dw

        # Draw the SWG waveguide:

        x = -self.period_swg * self.duty_swg / 2 / dbu
        for i in range(0, N_boxes):
            local_duty = (
                1.0 * (N_boxes - i) / N_boxes * self.duty_swg
                + 1.0 * i / N_boxes * self.duty_strip
            )
            local_period = to_itype(
                (
                    1.0 * (N_boxes - i) / N_boxes * self.period_swg
                    + 1.0 * i / N_boxes * self.period_strip
                ),
                dbu,
            )
            local_wg_width = (
                1.0 * (N_boxes - i) / N_boxes * wg_width_swg_taperend
                + 1.0 * i / N_boxes * wg_width_strip
            )
            if (i == 0) | (i == N_boxes):
                if debug:
                    print(
                        "local_duty: %s, local_period: %s, local_wg_width: %s"
                        % (local_duty, local_period, local_wg_width)
                    )
            local_box_width = int(round(local_period * local_duty))
            #      x = int(round((i * local_period - local_box_width/2)))
            if i != 0:
                box1 = Box(
                    x, -local_wg_width / 2, x + local_box_width, local_wg_width / 2
                )
            else:
                # Last SWG, that is a bit larger than the one connected to the taper
                box1 = Box(x, -wg_width_swg / 2, x + local_box_width, wg_width_swg / 2)
            shapes(LayerSiN).insert(box1)
            x = x + int(round((local_period)))

        # Taper
        if self.fishbone:
            taper_length = length
        pts = [
            Point(length - taper_length, -w1 / 2),
            Point(length - taper_length, w1 / 2),
            Point(length, w2 / 2),
            Point(length, -w2 / 2),
        ]
        shapes(LayerSiN).insert(Polygon(pts))

        # Pins on the waveguide:

        from SiEPIC._globals import PIN_LENGTH as pin_length

        w = to_itype(self.wg_width_swg, dbu)
        t = Trans(Trans.R0, 0, 0)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        w = to_itype(max(self.wg_width_strip, self.wg_width_taper), dbu)
        t = Trans(Trans.R0, length, 0)
        pin = Path([Point(-pin_length / 2, 0), Point(pin_length / 2, 0)], w)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu
        shape.text_halign = 2

        """
    # Compact model information
    t = Trans(Trans.R0, 0, 0)
    text = Text ('Lumerical_INTERCONNECT_library=Design kits/ebeam_v1.2', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, length/10, 0)
    text = Text ('Component=NO_MODEL_AVAILABLE', t)
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    t = Trans(Trans.R0, length/9, -w*2)
    text = Text \
      ('Spice_param:length=%.3fu period_swg=%.3fu period_strip=%.3fu wg_width_swg=%.3fu wg_width_strip=%.3fu duty_swg=%.3f duty_strip=%.3f ' %\
      (self.length, self.period_swg, (self.period_strip), self.wg_width_swg, self.wg_width_strip, self.duty_swg, self.duty_strip), t )
    shape = shapes(LayerDevRecN).insert(text)
    shape.text_size = 0.1/dbu
    blabla
    """

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        points = [pya.Point(0, 0), pya.Point(length, 0)]
        path = pya.Path(points, w * 5)
        shapes(LayerDevRecN).insert(path.simple_polygon())
