"""
Author:   Mustafa Hammood, 2022
          Mustafa@siepic.com; mustafa.hammood@dreamphotonics.com; mustafa@ece.ubc.ca
"""

import pya
from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils.layout import make_pin, make_devrec_label


class contra_directional_coupler(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(contra_directional_coupler, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # Button to launch separate window
        self.param(
            "documentation", self.TypeCallback, "Open documentation in web browser"
        )
        self.param("simulation", self.TypeCallback, "Launch simulation GUI")

        # declare the parameters
        self.param(
            "number_of_periods", self.TypeInt, "Number of grating periods", default=1000
        )
        self.param(
            "grating_period", self.TypeDouble, "Grating period (microns)", default=0.316
        )
        self.param("gap", self.TypeDouble, "Gap (microns)", default=0.10)
        self.param(
            "corrugation1_width",
            self.TypeDouble,
            "Waveguide 1 Corrugration width (microns)",
            default=0.05,
        )
        self.param(
            "corrugation2_width",
            self.TypeDouble,
            "Waveguide 2 Corrugration width (microns)",
            default=0.025,
        )
        self.param("AR", self.TypeBoolean, "Anti-Reflection Design", default=True)
        self.param(
            "sinusoidal",
            self.TypeBoolean,
            "Grating Type (Rectangular=False, Sinusoidal=True)",
            default=False,
        )
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.56)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.44)
        self.param("sbend", self.TypeBoolean, "Include S-bends", default=1)
        self.param("sbend_r", self.TypeDouble, "S-bend radius (microns)", default=15)
        self.param(
            "sbend_length", self.TypeDouble, "S-bend length (microns)", default=11
        )
        self.param(
            "apodization_index",
            self.TypeDouble,
            "Gaussian Apodization Index",
            default=10.0,
        )
        self.param("port_w", self.TypeDouble, "Port Waveguide width", default=0.5)
        self.param(
            "accuracy",
            self.TypeBoolean,
            "Simulation Accuracy (on = high, off = fast)",
            default=True,
            hidden=True,
        )
        self.param("layer", self.TypeLayer, "Waveguide Layer", default=TECHNOLOGY["Si"])
        self.param(
            "rib", self.TypeBoolean, "Use rib (ridge) waveguides?", default=False
        )
        self.param(
            "layer_rib",
            self.TypeLayer,
            "Rib Layer",
            default=TECHNOLOGY["Si - 90 nm rib"],
        )
        self.param("metal", self.TypeBoolean, "Use metal heaters?", default=False)
        self.param("heater_width", self.TypeDouble, "Metal heater width", default=3)
        self.param("metal_width", self.TypeDouble, "Metal contact width", default=5)
        self.param(
            "l_heater", self.TypeLayer, "Heater Layer", default=TECHNOLOGY["M1_heater"]
        )
        self.param(
            "l_metal",
            self.TypeLayer,
            "Metal contact Layer",
            default=TECHNOLOGY["M2_router"],
        )
        self.param(
            "pinrecm",
            self.TypeLayer,
            "PinRecM Layer (metal)",
            default=TECHNOLOGY["PinRecM"],
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )

    def callback(self, layout, name, states):
        """Callback for PCell, to launch documentation viewer
        https://www.klayout.de/doc/code/class_PCellDeclaration.html#method9
        """
        if name == "documentation":
            # Mustafa Hammood's repository for simulations of CDCs
            url = "https://github.com/SiEPIC/SiEPIC_Bragg_workshop"
            import webbrowser

            webbrowser.open_new(url)
        if name == "simulation":
            print("contraDC simulation window")
            from SiEPIC.simulation.contraDC.klayout_gui import cdc_gui

            cdc_gui()

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "contra_directional_coupler_%sN-%.1fnm period" % (
            self.number_of_periods,
            self.grating_period * 1000,
        )

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        import math

        try:
            from SiEPIC.utils.layout import layout_waveguide_sbend, layout_taper
        except:
            from siepic_tools.utils.layout import layout_waveguide_sbend, layout_taper

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerRib = ly.layer(self.layer_rib)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        shapes_wg = pya.Region()
        shapes_rib = pya.Region()

        from SiEPIC.extend import to_itype

        # Draw the Bragg grating (bottom):
        box_width = int(round(self.grating_period / 2 / dbu))
        grating_period = int(round(self.grating_period / dbu))

        w = to_itype(self.wg1_width, dbu)
        GaussianIndex = self.apodization_index
        half_w = w / 2
        half_corrugation_w = to_itype(self.corrugation1_width / 2, dbu)

        y_offset_top = -w / 2 - to_itype(self.gap / 2, dbu)

        if self.AR:
            misalignment = grating_period / 2
        else:
            misalignment = 0

        self.number_of_periods = int(self.number_of_periods)
        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                x = round((i * self.grating_period) / dbu)
                profileFunction = math.exp(
                    -0.5 * (2 * GaussianIndex * (i - N / 2) / (N)) ** 2
                )
                profile = (
                    int(round(self.corrugation1_width / 2 / dbu)) * profileFunction
                )
                box1 = pya.Box(
                    x, y_offset_top, x + box_width, y_offset_top + half_w + profile
                )
                pts1 = [pya.Point(x, y_offset_top)]
                pts3 = [pya.Point(x + misalignment, y_offset_top)]

                for i1 in range(0, npoints_sin + 1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(profile * math.sin(x1))
                    x1 = round(x1 / 2 / math.pi * grating_period)
                    pts1.append(pya.Point(x + x1, y_offset_top + half_w + y1))
                    pts3.append(
                        pya.Point(x + misalignment + x1, y_offset_top - half_w - y1)
                    )

                pts1.append(pya.Point(x + grating_period, y_offset_top))
                pts3.append(pya.Point(x + grating_period + misalignment, y_offset_top))

                shapes_wg += pya.Polygon(pts1)
                shapes_wg += pya.Polygon(pts3)

            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = pya.Box(
                    x + grating_period, y_offset_top, length, y_offset_top + half_w
                )
                # extra piece at the beginning:
                box3 = pya.Box(0, y_offset_top, misalignment, y_offset_top - half_w)

                shapes_wg += box2
                shapes_wg += box3

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period) / dbu))

                profileFunction = math.exp(
                    -0.5 * (2 * GaussianIndex * (i - N / 2) / (N)) ** 2
                )
                profile = (
                    int(round(self.corrugation1_width / 2 / dbu)) * profileFunction
                )

                box1 = pya.Box(
                    x,
                    y_offset_top,
                    x + box_width,
                    y_offset_top + to_itype(half_w + profile, dbu * 1000),
                )
                box2 = pya.Box(
                    x + box_width,
                    y_offset_top,
                    x + grating_period,
                    y_offset_top + to_itype(half_w - profile, dbu * 1000),
                )
                box3 = pya.Box(
                    x + misalignment,
                    y_offset_top,
                    x + box_width + misalignment,
                    y_offset_top + to_itype(-half_w - profile, dbu * 1000),
                )
                box4 = pya.Box(
                    x + box_width + misalignment,
                    y_offset_top,
                    x + grating_period + misalignment,
                    y_offset_top + to_itype(-half_w + profile, dbu * 1000),
                )

                shapes_wg += box1
                shapes_wg += box2
                shapes_wg += box3
                shapes_wg += box4
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = pya.Box(
                    x + grating_period, y_offset_top, length, y_offset_top + half_w
                )
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = pya.Box(0, y_offset_top, misalignment, y_offset_top - half_w)
                shapes_wg += box3

        vertical_offset = int(round(self.wg2_width / 2 / dbu)) + int(
            round(self.gap / 2 / dbu)
        )

        if misalignment > 0:
            t = pya.Trans(pya.Trans.R0, 0, vertical_offset)
        else:
            t = pya.Trans(pya.Trans.R0, 0, vertical_offset)

        # Draw the Bragg grating (top):
        box_width = int(round(self.grating_period / 2 / dbu))
        grating_period = int(round(self.grating_period / dbu))
        w = to_itype(self.wg2_width, dbu)
        half_w = w / 2
        half_corrugation_w = int(round(self.corrugation2_width / 2 / dbu))

        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                x = round((i * self.grating_period) / dbu)
                profileFunction = math.exp(
                    -0.5 * (2 * GaussianIndex * (i - N / 2) / (N)) ** 2
                )
                profile = (
                    int(round(self.corrugation2_width / 2 / dbu)) * profileFunction
                )
                box1 = pya.Box(x, 0, x + box_width, -half_w + profile).transformed(t)
                pts1 = [pya.Point(x, 0)]
                pts3 = [pya.Point(x + misalignment, 0)]
                for i1 in range(0, npoints_sin + 1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(profile * math.sin(x1))
                    x1 = round(x1 / 2 / math.pi * grating_period)
                    #          print("x: %s, y: %s" % (x1,y1))
                    pts1.append(pya.Point(x + x1, -half_w - y1))
                    pts3.append(pya.Point(x + misalignment + x1, +half_w + y1))
                pts1.append(pya.Point(x + grating_period, 0))
                pts3.append(pya.Point(x + grating_period + misalignment, 0))

                shapes_wg += pya.Polygon(pts1).transformed(t)
                shapes_wg += pya.Polygon(pts3).transformed(t)
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = pya.Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = pya.Box(0, 0, misalignment, half_w).transformed(t)
                shapes_wg += box3

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period) / dbu))
                profileFunction = math.exp(
                    -0.5 * (2 * GaussianIndex * (i - N / 2) / (N)) ** 2
                )
                profile = (
                    int(round(self.corrugation2_width / 2 / dbu)) * profileFunction
                )
                box1 = pya.Box(x, 0, x + box_width, -half_w - profile).transformed(t)
                box2 = pya.Box(
                    x + box_width, 0, x + grating_period, -half_w + profile
                ).transformed(t)
                box3 = pya.Box(
                    x + misalignment, 0, x + box_width + misalignment, half_w + profile
                ).transformed(t)
                box4 = pya.Box(
                    x + box_width + misalignment,
                    0,
                    x + grating_period + misalignment,
                    half_w - profile,
                ).transformed(t)

                shapes_wg += box1
                shapes_wg += box2
                shapes_wg += box3
                shapes_wg += box4

            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = pya.Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = pya.Box(0, 0, misalignment, half_w).transformed(t)
                shapes_wg += box3

        # Create the pins on the waveguides, as short paths:

        w1 = to_itype(self.wg1_width, dbu)
        w2 = to_itype(self.wg2_width, dbu)
        if self.sbend:
            port_w = to_itype(self.port_w, dbu)
            sbend_r = to_itype(self.sbend_r, dbu)
            sbend_length = to_itype(self.sbend_length, dbu)
            sbend_offset = (
                4 * port_w + port_w - (w1 + w2) / 2 - int(round(self.gap / dbu))
            )
            taper_length = 50 * max(abs(w1 - port_w), abs(w2 - port_w))

            t = pya.Trans(pya.Trans.R180, 0, y_offset_top)
            shapes_wg += layout_waveguide_sbend(
                self.cell,
                LayerSiN,
                t,
                w1,
                sbend_r,
                sbend_offset,
                sbend_length,
                insert=False,
                dbu=dbu,
            )
            t = pya.Trans(
                pya.Trans.R0, -sbend_length - taper_length, y_offset_top - sbend_offset
            )
            shapes_wg += layout_taper(
                self.cell, LayerSiN, t, port_w, w1, taper_length, insert=False
            )
            x = -sbend_length - taper_length
            y = y_offset_top - sbend_offset
            make_pin(self.cell, "opt1", [x, y], port_w, LayerPinRecN, 180)

            x = -taper_length - sbend_length
            y = vertical_offset
            make_pin(self.cell, "opt2", [x, y], port_w, LayerPinRecN, 180)

            x = length + sbend_length + taper_length
            y = y_offset_top - sbend_offset
            # i don't know why int(x) works but x doesnt
            # future debugger, email mustafa hammood :)
            make_pin(self.cell, "opt3", [int(x), y], port_w, LayerPinRecN, 0)

            x = length + taper_length + sbend_length
            y = vertical_offset
            make_pin(self.cell, "opt4", [int(x), y], port_w, LayerPinRecN, 0)

            t = pya.Trans(pya.Trans.R180, 0, vertical_offset)
            shapes_wg += layout_taper(
                self.cell, LayerSiN, t, w2, w2, sbend_length / 2, insert=False
            )
            t = pya.Trans(pya.Trans.R180, -sbend_length / 2, vertical_offset)
            shapes_wg += layout_taper(
                self.cell,
                LayerSiN,
                t,
                w2,
                port_w,
                taper_length + sbend_length / 2,
                insert=False,
            )

            t = pya.Trans(pya.Trans.R0, length, y_offset_top)
            shapes_wg += layout_waveguide_sbend(
                self.cell,
                LayerSiN,
                t,
                w1,
                sbend_r,
                -sbend_offset,
                sbend_length,
                insert=False,
                dbu=dbu,
            )
            t = pya.Trans(pya.Trans.R0, length + sbend_length, y_offset_top - sbend_offset)
            shapes_wg += layout_taper(
                self.cell, LayerSiN, t, w1, port_w, taper_length, insert=False
            )

            t = pya.Trans(pya.Trans.R0, length, vertical_offset)
            shapes_wg += layout_taper(
                self.cell, LayerSiN, t, w2, w2, sbend_length / 2, insert=False
            )
            t = pya.Trans(pya.Trans.R0, length + sbend_length / 2, vertical_offset)
            shapes_wg += layout_taper(
                self.cell,
                LayerSiN,
                t,
                w2,
                port_w,
                taper_length + sbend_length / 2,
                insert=False,
            )

        else:
            x = 0
            y = y_offset_top
            make_pin(self.cell, "opt1", [x, y], w1, LayerPinRecN, 180)

            y = vertical_offset
            make_pin(self.cell, "opt2", [x, y], w2, LayerPinRecN, 180)

            x = length
            y = y_offset_top
            make_pin(self.cell, "opt3", [int(x), y], w1, LayerPinRecN, 0)

            x = length
            y = vertical_offset
            make_pin(self.cell, "opt4", [int(x), y], w2, LayerPinRecN, 0)

        # Compact model information. Create the devrec library labels
        make_devrec_label(
            self.cell, "EBeam", "contra_directional_coupler", ly.layer(self.devrec)
        )

        text = pya.Text(
            "Spice_param:number_of_periods=%s grating_period=%.4fu wg1_width=%.3fu wg2_width=%.3fu corrugation1_width=%.3fu corrugation2_width=%.3fu gap=%.3fu apodization_index=%.3f AR=%s sinusoidal=%s accuracy=%s"
            % (
                self.number_of_periods,
                self.grating_period,
                self.wg1_width,
                self.wg2_width,
                self.corrugation1_width,
                self.corrugation2_width,
                self.gap,
                self.apodization_index,
                int(self.AR),
                int(self.sinusoidal),
                int(self.accuracy),
            ),
            t,
        )
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1 / dbu

        if self.metal:
            # add heater element
            heater_width = to_itype(self.heater_width, dbu)
            box = pya.Box(
                pya.Point(0, heater_width / 2), pya.Point(length, -heater_width / 2)
            )
            shapes(ly.layer(self.l_heater)).insert(box)

            # add metal contact element (left and right)
            metal_width = to_itype(self.metal_width, dbu)
            box = pya.Box(
                pya.Point(0, heater_width / 2),
                pya.Point(metal_width, -heater_width / 2),
            )
            shapes(ly.layer(self.l_metal)).insert(box)
            box = pya.Box(
                pya.Point(length, heater_width / 2),
                pya.Point(length - metal_width, -heater_width / 2),
            )
            shapes(ly.layer(self.l_metal)).insert(box)

            # add metal contact pins
            x = metal_width / 2 * dbu
            y = -heater_width / 2 * dbu
            make_pin(
                self.cell, "elec1", [x, y], metal_width, ly.layer(self.pinrecm), 270
            )
            x = (length - metal_width / 2) * dbu
            make_pin(
                self.cell, "elec2", [x, y], metal_width, ly.layer(self.pinrecm), 270
            )

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        if self.sbend:
            box = pya.Box(
                pya.Point(-taper_length - sbend_length, vertical_offset + 3 * port_w),
                pya.Point(
                    length + taper_length + sbend_length,
                    y_offset_top - sbend_offset - 3 * port_w,
                ),
            )
        else:
            box = pya.Box(
                pya.Point(0, vertical_offset + 3 * (w1 + w2) / 2),
                pya.Point(length, y_offset_top - 3 * (w1 + w2) / 2),
            )
        DevRecBox = box
        shapes(LayerDevRecN).insert(box)

        # Draw the waveguide layer
        if self.rib == False:
            shapes(LayerSiN).insert(shapes_wg)
        else:  # turn shape into a rib waveguide
            region_devrec = pya.Region(DevRecBox)
            region_devrec2 = pya.Region(DevRecBox).size(1500)
            shapes_rib += shapes_wg
            shapeRib = (
                shapes_rib.size(1400) - shapes_wg - (region_devrec2 - region_devrec)
            )

            shapes(LayerRib).insert(shapeRib)
            shapes(LayerRib).insert(shapes_wg)
            shapes(LayerSiN).insert(shapes_wg)
