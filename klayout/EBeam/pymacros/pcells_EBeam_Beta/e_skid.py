import pya
from . import *
from SiEPIC.utils import get_technology_by_name
from SiEPIC._globals import PIN_LENGTH as pin_length
from pya import DPolygon
import math

# ====================================================================================================
# File:     e_skid.py
# Author:   Hang (Bobby) Zou
# Purpose:  PCell in EBeam library for a common parallel e-skid design that have adjustable period
#           and fill factor
# Version:  V2.0
# Date:     2023-11-09
# ====================================================================================================


class e_skid(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        super(e_skid, self).__init__()
        self.technology_name = "EBeam"

        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # e_skid Parameters:
        # core parameter
        self.param(
            "divider0", self.TypeNone, "==============Core Parameter=============="
        )

        self.param("w", self.TypeDouble, "Core Waveguide Width [um]", default=0.3)

        self.param(
            "divider1", self.TypeNone, "==============Clad Parameter=============="
        )

        # clad parameter
        self.param("p", self.TypeDouble, "e-skid Period [um]", default=0.1)
        self.param("ff", self.TypeDouble, "e-skid Fill Factor [0.2-0.8]", default=0.5)
        self.param("p_num", self.TypeInt, "e-skid Period Number", default=5)
        self.param(
            "length", self.TypeDouble, "Length of e-skid Waveguide [um]", default=10
        )

        self.param(
            "divider2", self.TypeNone, "==============Taper Parameter============="
        )

        # taper
        self.param("taper_True", self.TypeBoolean, "Taper [T/F]", default=True)
        self.param(
            "taperL", self.TypeDouble, "Strip -> e-skid Taper Length [um]", default=5
        )
        self.param("taperW", self.TypeDouble, "Strip Width [um]", default=0.5)

        self.param(
            "divider3", self.TypeNone, "============Extended Clad Parameter=========="
        )

        # extended clad parameter
        self.param(
            "clad_taper_L", self.TypeDouble, "Extended e-skid Length [um]", default=5
        )
        self.param(
            "clad_taper_angle",
            self.TypeDouble,
            "Extended e-skid Angle [degree]",
            default=2,
        )

        self.param("divider4", self.TypeNone, "=====================================")

        # Layer Parameters - Don't touch
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param(
            "oxideopen",
            self.TypeLayer,
            "Oxide Open Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "configurable_e_skid"

    # Creating the layout
    def produce_impl(self):
        # Layout Parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        w = self.w  # Core Waveguide Width [um]
        p = self.p  # e-skid Period [um]
        ff = self.ff  # e-skid Duty Cycle [%]
        p_num = self.p_num  # e-skid Period Number
        length = self.length  # e-skid Waveguide Length [um]

        taper_True = self.taper_True  # e-skid Taper [T/F]
        taperW = self.taperW  # e-skid Taper Width [um]
        taperL = self.taperL  # e-skid Taper Length [um]

        clad_taper_L = self.clad_taper_L  # Extended e-skid length [nm]
        clad_taper_angle_radians = (
            self.clad_taper_angle * math.pi / 180
        )  # Extended e-skid angle [degrees]

        ###############################
        ########### e-skid ############
        ###############################

        # 1. e-skid main body

        # x, y coordinates of the core
        x_core = [0, length, length, 0]
        y_core = [-w / 2, -w / 2, w / 2, w / 2]

        dpts = [
            pya.DPoint(x_core[i], y_core[i]) for i in range(len(x_core))
        ]  # Core body
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1 / dbu))
        shapes(LayerSiN).insert(element)

        # draw multiple clad for both top and bottom
        for i in range(1, p_num + 1):
            # x, y coordinates of the top clad
            x_clad_top = [0, length, length, 0]
            y_clad_top = [
                w / 2 + i * p - (p * ff),
                w / 2 + i * p - (p * ff),
                w / 2 + i * p,
                w / 2 + i * p,
            ]

            dpts = [
                pya.DPoint(x_clad_top[i], y_clad_top[i]) for i in range(len(x_clad_top))
            ]  # Core body
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1 / dbu))
            shapes(LayerSiN).insert(element)

            # x, y coordinates of the bottom clad
            x_clad_bottom = [0, length, length, 0]
            y_clad_bottom = [
                -w / 2 - i * p + (p * ff),
                -w / 2 - i * p + (p * ff),
                -w / 2 - i * p,
                -w / 2 - i * p,
            ]

            dpts = [
                pya.DPoint(x_clad_bottom[i], y_clad_bottom[i])
                for i in range(len(x_clad_bottom))
            ]  # Core body
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1 / dbu))
            shapes(LayerSiN).insert(element)

        # 2. taper + Pins

        if taper_True:
            # Top clad
            if clad_taper_L > taperL:
                # Prevent the clad_taper_L to be larger than taperL
                clad_taper_L = taperL

            # Calculate the required offset
            w_offset = taperW * clad_taper_L / taperL

            # fetch the taper angle at the set point
            taper_angle = math.atan(((taperW - w) / 2) / (taperL))

            if clad_taper_angle_radians <= taper_angle:
                clad_taper_angle_radians = taper_angle

            for i in range(1, p_num + 1):
                # draw the right clad, angle method
                # locate the end points of the extended clad
                clad_end_point_position = (
                    w / 2
                    + i * p
                    + i * (clad_taper_L * math.tan(clad_taper_angle_radians))
                )

                # x, y coordinates of the top clad
                x_clad_top = [
                    length,
                    length + clad_taper_L,
                    length + clad_taper_L,
                    length,
                ]
                y_clad_top = [
                    w / 2 + i * p - (p * ff),
                    clad_end_point_position - (p * ff),
                    clad_end_point_position,
                    w / 2 + i * p,
                ]

                dpts = [
                    pya.DPoint(x_clad_top[i], y_clad_top[i])
                    for i in range(len(x_clad_top))
                ]  # Core body
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1 / dbu))
                shapes(LayerSiN).insert(element)

                # x, y coordinates of the bottom clad
                x_clad_bottom = [
                    length,
                    length + clad_taper_L,
                    length + clad_taper_L,
                    length,
                ]
                y_clad_bottom = [
                    -w / 2 - i * p + (p * ff),
                    -clad_end_point_position + (p * ff),
                    -clad_end_point_position,
                    -w / 2 - i * p,
                ]

                dpts = [
                    pya.DPoint(x_clad_bottom[i], y_clad_bottom[i])
                    for i in range(len(x_clad_bottom))
                ]  # Core body
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1 / dbu))
                shapes(LayerSiN).insert(element)

                # draw the left clad, angle method
                # locate the end points of the extended clad
                clad_end_point_position = (
                    w / 2
                    + i * p
                    + i * (clad_taper_L * math.tan(clad_taper_angle_radians))
                )

                # x, y coordinates of the top clad
                x_clad_top = [0, -clad_taper_L, -clad_taper_L, 0]
                y_clad_top = [
                    w / 2 + i * p - (p * ff),
                    clad_end_point_position - (p * ff),
                    clad_end_point_position,
                    w / 2 + i * p,
                ]

                dpts = [
                    pya.DPoint(x_clad_top[i], y_clad_top[i])
                    for i in range(len(x_clad_top))
                ]  # Core body
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1 / dbu))
                shapes(LayerSiN).insert(element)

                # x, y coordinates of the bottom clad
                x_clad_bottom = [0, -clad_taper_L, -clad_taper_L, 0]
                y_clad_bottom = [
                    -w / 2 - i * p + (p * ff),
                    -clad_end_point_position + (p * ff),
                    -clad_end_point_position,
                    -w / 2 - i * p,
                ]

                dpts = [
                    pya.DPoint(x_clad_bottom[i], y_clad_bottom[i])
                    for i in range(len(x_clad_bottom))
                ]  # Core body
                dpolygon = DPolygon(dpts)
                element = Polygon.from_dpoly(dpolygon * (1 / dbu))
                shapes(LayerSiN).insert(element)

            # left taper
            x_taper_left = [0, 0, -taperL, -taperL]
            y_taper_left = [-w / 2, w / 2, taperW / 2, -taperW / 2]

            dpts = [
                pya.DPoint(x_taper_left[i], y_taper_left[i])
                for i in range(len(x_taper_left))
            ]  # Core body
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1 / dbu))
            shapes(LayerSiN).insert(element)

            # right taper
            x_taper_right = [length, length, length + taperL, length + taperL]
            y_taper_right = [-w / 2, w / 2, taperW / 2, -taperW / 2]

            dpts = [
                pya.DPoint(x_taper_right[i], y_taper_right[i])
                for i in range(len(x_taper_right))
            ]  # Core body
            dpolygon = DPolygon(dpts)
            element = Polygon.from_dpoly(dpolygon * (1 / dbu))
            shapes(LayerSiN).insert(element)

            # Adding Pins for mating
            # Pin 1
            t = pya.DTrans(pya.Trans.R90, -taperL / dbu, 0 / dbu)
            pin = pya.Path(
                [pya.DPoint(0, -pin_length / 2), pya.DPoint(0, pin_length / 2)],
                taperW / dbu,
            )
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text("opt1", pya.DTrans(pya.Trans.R0, -taperL / dbu, 0 / dbu))
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.2 / dbu

            # Pin 2
            t = pya.DTrans(pya.Trans.R270, (taperL + length) / dbu, 0 / dbu)
            pin = pya.Path(
                [pya.DPoint(0, -pin_length / 2), pya.DPoint(0, pin_length / 2)],
                taperW / dbu,
            )
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text(
                "opt2", pya.DTrans(pya.Trans.R0, (taperL + length) / dbu, 0 / dbu)
            )
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.2 / dbu

            # Devbox
            dev = pya.DBox(
                -taperL,
                clad_end_point_position + 0.5,
                length + taperL,
                -clad_end_point_position - 0.5,
            )

            shapes(LayerDevRecN).insert(dev)

        else:
            # Adding Pins for mating
            # Pin 1
            t = pya.DTrans(pya.Trans.R90, 0, 0 / dbu)
            pin = pya.Path(
                [pya.DPoint(0, -pin_length / 2), pya.DPoint(0, pin_length / 2)], w / dbu
            )
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text("opt1", pya.DTrans(pya.Trans.R0, 0, 0 / dbu))
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.2 / dbu

            # Pin 2
            t = pya.DTrans(pya.Trans.R270, length / dbu, 0 / dbu)
            pin = pya.Path(
                [pya.DPoint(0, -pin_length / 2), pya.DPoint(0, pin_length / 2)], w / dbu
            )
            pin_t = pin.transformed(t)
            shapes(LayerPinRecN).insert(pin_t)
            text = pya.Text("opt2", pya.DTrans(pya.Trans.R0, length / dbu, 0 / dbu))
            shape = shapes(LayerPinRecN).insert(text)
            shape.text_size = 0.2 / dbu

            # Devbox
            dev = pya.DBox(0, w / 2 + p_num * p + 0.5, length, -w / 2 - p_num * p - 0.5)

            shapes(LayerDevRecN).insert(dev)


# ====================================================================================================
# END OF DOCUMENT
# ====================================================================================================
