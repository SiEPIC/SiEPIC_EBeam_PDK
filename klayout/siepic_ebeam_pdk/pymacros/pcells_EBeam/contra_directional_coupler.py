"""
Author:   Mustafa Hammood, 2021
          Mustafa@siepic.com; mustafa.hammood@dreamphotonics.com; mustafa@ece.ubc.ca
"""

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from SiEPIC.utils.layout import make_pin, make_devrec_label


class contra_directional_coupler(pya.PCellDeclarationHelper):

    def __init__(self):
        # Important: initialize the super class
        super(contra_directional_coupler, self).__init__()
        TECHNOLOGY = get_technology_by_name('EBeam')

        # declare the parameters
        self.param("number_of_periods", self.TypeInt, "Number of grating periods", default=500)
        self.param("grating_period", self.TypeDouble,
                   "Grating period (microns)", default=0.317)
        self.param("gap", self.TypeDouble, "Gap (microns)", default=0.15)
        self.param("corrugation_width1", self.TypeDouble,
                   "Waveguide 1 Corrugration width (microns)", default=0.03)
        self.param("corrugation_width2", self.TypeDouble,
                   "Waveguide 2 Corrugration width (microns)", default=0.06)
        self.param("AR", self.TypeBoolean, "Anti-Reflection Design", default=True)
        self.param("sinusoidal", self.TypeBoolean,
                   "Grating Type (Rectangular=False, Sinusoidal=True)", default=False)
        self.param("wg1_width", self.TypeDouble, "Waveguide 1 width", default=0.45)
        self.param("wg2_width", self.TypeDouble, "Waveguide 2 width", default=0.55)
        self.param("sbend", self.TypeBoolean, "Include S-bends", default=1)
        self.param("sbend_r", self.TypeDouble, "S-bend radius (microns)", default=15)
        self.param("sbend_length", self.TypeDouble, "S-bend length (microns)", default=11)
        self.param("apodization_index", self.TypeDouble,
                   "Gaussian Apodization Index", default=2.8)
        self.param("port_w", self.TypeDouble, "Port Waveguide width", default=0.5)
        self.param("accuracy", self.TypeBoolean,
                   "Simulation Accuracy (on = high, off = fast)", default=True)
        self.param("layer", self.TypeLayer, "Waveguide Layer", default=TECHNOLOGY['Waveguide'])
        self.param("rib", self.TypeBoolean, "Use rib (ridge) waveguides?", default=False)
        self.param("layer_rib", self.TypeLayer, "Rib Layer",
                   default=TECHNOLOGY['Si - 90 nm rib'])
        self.param("pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY['PinRec'])
        self.param("devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY['DevRec'])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "contra_directional_coupler_%sN-%.1fnm period" % \
            (self.number_of_periods, self.grating_period*1000)

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
        box_width = int(round(self.grating_period/2/dbu))
        grating_period = int(round(self.grating_period/dbu))

        w = to_itype(self.wg1_width, dbu)
        GaussianIndex = self.apodization_index
        half_w = w/2
        half_corrugation_w = to_itype(self.corrugation_width1/2, dbu)

        y_offset_top = -w/2 - to_itype(self.gap/2, dbu)

        if self.AR:
            misalignment = grating_period/2
        else:
            misalignment = 0

        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                x = (round((i * self.grating_period)/dbu))
                profileFunction = math.exp(-0.5*(2*GaussianIndex*(i-N/2)/(N))**2)
                profile = int(round(self.corrugation_width1/2/dbu))*profileFunction
                box1 = Box(x, y_offset_top, x + box_width, y_offset_top + half_w+profile)
                pts1 = [Point(x, y_offset_top)]
                pts3 = [Point(x + misalignment, y_offset_top)]

                for i1 in range(0, npoints_sin+1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(profile*math.sin(x1))
                    x1 = round(x1/2/math.pi*grating_period)
                    pts1.append(Point(x + x1, y_offset_top + half_w+y1))
                    pts3.append(Point(x + misalignment + x1, y_offset_top - half_w-y1))

                pts1.append(Point(x + grating_period, y_offset_top))
                pts3.append(Point(x + grating_period + misalignment, y_offset_top))

                shapes_wg += Polygon(pts1)
                shapes_wg += Polygon(pts3)

            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, y_offset_top, length, y_offset_top + half_w)
                # extra piece at the beginning:
                box3 = Box(0, y_offset_top, misalignment, y_offset_top - half_w)

                shapes_wg += box2
                shapes_wg += box3

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period)/dbu))

                profileFunction = math.exp(-0.5*(2*GaussianIndex*(i-N/2)/(N))**2)
                profile = int(round(self.corrugation_width1/2/dbu))*profileFunction

                box1 = Box(x, y_offset_top, x + box_width, y_offset_top +
                           to_itype(half_w+profile, dbu*1000))
                box2 = Box(x + box_width, y_offset_top, x + grating_period,
                           y_offset_top + to_itype(half_w-profile, dbu*1000))
                box3 = Box(x + misalignment, y_offset_top, x + box_width +
                           misalignment, y_offset_top + to_itype(-half_w-profile, dbu*1000))
                box4 = Box(x + box_width + misalignment, y_offset_top, x + grating_period +
                           misalignment, y_offset_top + to_itype(-half_w+profile, dbu*1000))

                shapes_wg += box1
                shapes_wg += box2
                shapes_wg += box3
                shapes_wg += box4
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, y_offset_top, length, y_offset_top + half_w)
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = Box(0, y_offset_top, misalignment, y_offset_top - half_w)
                shapes_wg += box3

        vertical_offset = int(round(self.wg2_width/2/dbu))+int(round(self.gap/2/dbu))

        if misalignment > 0:
            t = Trans(Trans.R0, 0, vertical_offset)
        else:
            t = Trans(Trans.R0, 0, vertical_offset)

        # Draw the Bragg grating (top):
        box_width = int(round(self.grating_period/2/dbu))
        grating_period = int(round(self.grating_period/dbu))
        w = to_itype(self.wg2_width, dbu)
        half_w = w/2
        half_corrugation_w = int(round(self.corrugation_width2/2/dbu))

        N = self.number_of_periods
        if self.sinusoidal:
            npoints_sin = 40
            for i in range(0, self.number_of_periods):
                x = (round((i * self.grating_period)/dbu))
                profileFunction = math.exp(-0.5*(2*GaussianIndex*(i-N/2)/(N))**2)
                profile = int(round(self.corrugation_width2/2/dbu))*profileFunction
                box1 = Box(x, 0, x + box_width, -half_w+profile).transformed(t)
                pts1 = [Point(x, 0)]
                pts3 = [Point(x + misalignment, 0)]
                for i1 in range(0, npoints_sin+1):
                    x1 = i1 * 2 * math.pi / npoints_sin
                    y1 = round(profile*math.sin(x1))
                    x1 = round(x1/2/math.pi*grating_period)
#          print("x: %s, y: %s" % (x1,y1))
                    pts1.append(Point(x + x1, -half_w-y1))
                    pts3.append(Point(x + misalignment + x1, +half_w+y1))
                pts1.append(Point(x + grating_period, 0))
                pts3.append(Point(x + grating_period + misalignment, 0))

                shapes_wg += Polygon(pts1).transformed(t)
                shapes_wg += Polygon(pts3).transformed(t)
            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, half_w).transformed(t)
                shapes_wg += box3

        else:
            for i in range(0, self.number_of_periods):
                x = int(round((i * self.grating_period)/dbu))
                profileFunction = math.exp(-0.5*(2*GaussianIndex*(i-N/2)/(N))**2)
                profile = int(round(self.corrugation_width2/2/dbu))*profileFunction
                box1 = Box(x, 0, x + box_width, -half_w-profile).transformed(t)
                box2 = Box(x + box_width, 0, x + grating_period, -
                           half_w+profile).transformed(t)
                box3 = Box(x + misalignment, 0, x + box_width +
                           misalignment, half_w+profile).transformed(t)
                box4 = Box(x + box_width + misalignment, 0, x + grating_period +
                           misalignment, half_w-profile).transformed(t)

                shapes_wg += box1
                shapes_wg += box2
                shapes_wg += box3
                shapes_wg += box4

            length = x + grating_period + misalignment
            if misalignment > 0:
                # extra piece at the end:
                box2 = Box(x + grating_period, 0, length, -half_w).transformed(t)
                shapes_wg += box2
                # extra piece at the beginning:
                box3 = Box(0, 0, misalignment, half_w).transformed(t)
                shapes_wg += box3

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        w1 = to_itype(self.wg1_width, dbu)
        w2 = to_itype(self.wg2_width, dbu)
        if self.sbend:

            port_w = to_itype(self.port_w, dbu)
            sbend_r = to_itype(self.sbend_r, dbu)
            sbend_length = to_itype(self.sbend_length, dbu)
            sbend_offset = 4*port_w + port_w - (w1+w2)/2 - int(round(self.gap/dbu))
            taper_length = 50*max(abs(w1-port_w), abs(w2-port_w))

            t = Trans(Trans.R180, 0, y_offset_top)
            shapes_wg += layout_waveguide_sbend(self.cell, LayerSiN,
                                                t, w1, sbend_r, sbend_offset, sbend_length, insert=False)
            t = Trans(Trans.R0, -sbend_length-taper_length, y_offset_top-sbend_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t,  port_w,
                                      w1, taper_length, insert=False)
            x = -sbend_length-taper_length
            y = y_offset_top-sbend_offset
            make_pin(self.cell, "opt1", [x, y], port_w, LayerPinRecN, 180)

            x = -taper_length-sbend_length
            y = vertical_offset
            make_pin(self.cell, "opt2", [x, y], port_w, LayerPinRecN, 180)

            x = length+sbend_length+taper_length
            y = y_offset_top-sbend_offset
            # i don't know why int(x) works but x doesnt
            # future debugger, email mustafa hammood :)
            make_pin(self.cell, "opt3", [int(x), y], port_w, LayerPinRecN, 0)

            x = length+taper_length+sbend_length
            y = vertical_offset
            make_pin(self.cell, "opt4", [int(x), y], port_w, LayerPinRecN, 0)

            t = Trans(Trans.R180, 0, vertical_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t,  w2,
                                      w2, sbend_length/2, insert=False)
            t = Trans(Trans.R180, -sbend_length/2, vertical_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t,  w2,
                                      port_w, taper_length+sbend_length/2, insert=False)


            t = Trans(Trans.R0, length, y_offset_top)
            shapes_wg += layout_waveguide_sbend(self.cell, LayerSiN, t,
                                                w1, sbend_r, -sbend_offset, sbend_length, insert=False)
            t = Trans(Trans.R0, length+sbend_length, y_offset_top-sbend_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t, w1,
                                      port_w, taper_length, insert=False)


            t = Trans(Trans.R0, length, vertical_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t,  w2,
                                      w2, sbend_length/2, insert=False)
            t = Trans(Trans.R0, length+sbend_length/2, vertical_offset)
            shapes_wg += layout_taper(self.cell, LayerSiN, t,  w2,
                                      port_w, taper_length+sbend_length/2, insert=False)

        else:
            x = 0
            y = y_offset_top
            make_pin(self.cell, "opt1", [x, y], w1, LayeOrPinRecN, 180)

            y = vertical_offset
            make_pin(self.cell, "opt2", [x, y], w2, LayerPinRecN, 180)

            x = length
            y = y_offset_top
            make_pin(self.cell, "opt3", [int(x), y], w1, LayerPinRecN, 0)

            x = length
            y = vertical_offset
            make_pin(self.cell, "opt4", [int(x), y], w2, LayerPinRecN, 0)

        # Compact model information. Create the devrec library labels
        make_devrec_label(self.cell, "EBeam", "contra_directional_coupler",
                          ly.layer(self.devrec))

        text = Text('Spice_param:number_of_periods=%s grating_period=%.3fu wg1_width=%.3fu wg2_width=%.3fu corrugation_width1=%.3fu corrugation_width2=%.3fu gap=%.3fu apodization_index=%.3f AR=%s sinusoidal=%s accuracy=%s' %
                    (self.number_of_periods, self.grating_period, self.wg1_width, self.wg2_width, self.corrugation_width1, self.corrugation_width2, self.gap, self.apodization_index, int(self.AR), int(self.sinusoidal), int(self.accuracy)), t)
        shape = shapes(LayerDevRecN).insert(text)
        shape.text_size = 0.1/dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        if self.sbend:
            box = pya.Box(pya.Point(-taper_length-sbend_length, vertical_offset+3*port_w),
                          pya.Point(length+taper_length+sbend_length, y_offset_top-sbend_offset-3*port_w))
        else:
            box = pya.Box(pya.Point(0, vertical_offset+3*(w1+w2)/2),
                          pya.Point(length, y_offset_top-3*(w1+w2)/2))
        DevRecBox = box
        shapes(LayerDevRecN).insert(box)

        # Draw the waveguide layer
        if self.rib == False:
            shapes(LayerSiN).insert(shapes_wg)
        else:  # turn shape into a rib waveguide
            region_devrec = Region(DevRecBox)
            region_devrec2 = Region(DevRecBox).size(1500)
            shapes_rib += shapes_wg
            shapeRib = shapes_rib.size(1400) - shapes_wg - (region_devrec2-region_devrec)

            shapes(LayerRib).insert(shapeRib)
            shapes(LayerSiN).insert(shapes_wg)
