from . import *
import pya
from SiEPIC.utils import get_technology_by_name, arc_wg_xy
from SiEPIC._globals import PIN_LENGTH as pin_length
from pya import DPolygon


class e_skid_ring(pya.PCellDeclarationHelper):
    """
    Author: Ben Cohen (UBC), Hang Bobby Zou (UBC)
    bcohenkl@ece.ubc.ca
    Nov 9, 2023

    - This Pcell creates a single-bus ring resonator modified with e-skid concentric rings
    - Design control over number of inner/outer concentric rings. Gap between two rings and width is parameterized
    as an input list.
      - If a 0 is found in any entry of the list, the cell will automatically delete every element in the list
      - If the number of entries in the gap and width lists are different, the list with the minimum number of elements is considered

    - Controllable coupling. Bus length is designed as the outer most radius of the e-skid ring resonator
    """

    def __init__(self):
        # Important: initialize the super class
        super(e_skid_ring, self).__init__()
        self.technology_name = "EBeam"
        TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Main Ring Parameters
        self.param("r", self.TypeDouble, "Ring Radii [um]", default=10)
        self.param("w", self.TypeDouble, "Ring Waveguide Width [um]", default=0.5)
        self.param("cg", self.TypeDouble, "Coupling Gap [um]", default=0.2)

        # Bus Parameters:
        self.param("bus_w", self.TypeDouble, "Bus Waveguide Width [um]", default=0.5)

        # e-skid parameter
        self.param(
            "gap_out", self.TypeList, "Outer Gap List [um] (0 if none)", default=[0]
        )
        self.param(
            "w_out", self.TypeList, "Outer Width List [um] (0 if none)", default=[0]
        )

        self.param(
            "gap_in",
            self.TypeList,
            "Inner Gap List [um] (0 if none)",
            default=[0.3, 0.3],
        )
        self.param(
            "w_in",
            self.TypeList,
            "Inner Width List [um] (0 if none)",
            default=[0.1, 0.1],
        )

        # Layer Parameters
        self.param(
            "layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"], hidden=True
        )
        self.param(
            "pinrec",
            self.TypeLayer,
            "PinRec Layer",
            default=TECHNOLOGY["PinRec"],
            hidden=True,
        )
        self.param(
            "devrec",
            self.TypeLayer,
            "DevRec Layer",
            default=TECHNOLOGY["DevRec"],
            hidden=True,
        )
        self.param(
            "oxideopen",
            self.TypeLayer,
            "Oxide Open Layer",
            default=TECHNOLOGY["Oxide open (to BOX)"],
            hidden=True,
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "ring_resonator_with_e_skid_pillar"

    # Creating the layout
    def produce_impl(self):
        # Layout Parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        # Layers
        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Main Ring Parameters
        r = self.r  # Ring radii [um]
        w = self.w  # Ring waveguide width [um]
        cg = self.cg  # Coupling gap

        # Bus Parameters:
        bus_w = self.bus_w  # Bus width [um]
        bus_l = 2 * (r + w)  # Bus length [um]

        # e-skid parameters
        gap_out = self.gap_out  # Gap between different widths for rings outside of the main ring resonator [um]
        w_out = self.w_out  # Width of each ring outside of the main ring resonator [um]
        gap_in = self.gap_in  # Gap between different widths for rings inside of the main ring resonator [um]
        w_in = self.w_in  # Width of each ring inside of the main ring resonator [um]

        # Converting the list elements from str (klayout default) to float
        # No entries in either array should be 0, deleting every entry after 0 is found
        for i in range(len(w_out)):
            w_out[i] = float(w_out[i])
            if w_out[i] == 0:
                w_out = w_out[:i]
                break

        for i in range(len(gap_out)):
            gap_out[i] = float(gap_out[i])
            if gap_out[i] == 0:
                w_out = w_out[:i]
                break

        for i in range(len(w_in)):
            w_in[i] = float(w_in[i])
            if w_in[i] == 0:
                w_in = w_in[:i]
                break

        for i in range(len(gap_in)):
            gap_in[i] = float(gap_in[i])
            if gap_in[i] == 0:
                gap_in = gap_in[:i]
                break

        # Ring Resonator
        if r != 0:
            shapes(LayerSiN).insert(arc_wg_xy(0, 0, (r + w / 2) / dbu, w / dbu, 0, 360))

        # Bus Waveguide
        bus_x = [-bus_l / 2, bus_l / 2, bus_l / 2, -bus_l / 2]
        bus_y = [r + w + cg, r + w + cg, r + w + cg + bus_w, r + w + cg + bus_w]

        dpts = [pya.DPoint(bus_x[i], bus_y[i]) for i in range(len(bus_x))]  # Core body
        dpolygon = DPolygon(dpts)
        element = Polygon.from_dpoly(dpolygon * (1 / dbu))
        shapes(LayerSiN).insert(element)

        # Adding outer concetric rings
        """
        rad0_out = r + w
        for i in range(min(len(gap_out), len(w_out))):
            ring = pya.Region()
            ring.insert(arc_wg_xy(0, 0, (rad0_out + gap_out[i] + w_out[i]/2)/dbu, w_out[i]/dbu, 0, 360))

            # CONSIDERATION FOR TAPERS
            box_subtract = 
            shapes(LayerSiN).insert(ring)

            #shapes(LayerSiN).insert(arc_wg_xy(0, 0, (rad0_out + gap_out[i] + w_out[i]/2)/dbu, w_out[i]/dbu, 0, 360))
            rad0_out = rad0_out + gap_out[i] + w_out[i]
        """

        # Adding inner concetric rings
        if r != 0:
            rad0_in = r
            for i in range(min(len(gap_in), len(w_in))):
                ring = pya.Region()
                ring.insert(
                    arc_wg_xy(
                        0,
                        0,
                        (rad0_in - gap_in[i] - w_in[i] / 2) / dbu,
                        w_in[i] / dbu,
                        0,
                        360,
                    )
                )
                shapes(LayerSiN).insert(ring)

                rad0_in = rad0_in - gap_in[i] - w_in[i]

        # Pins for mating:
        t = pya.DTrans(
            pya.Trans.R90, min(bus_x) / dbu, (min(bus_y) + max(bus_y)) / 2 / dbu
        )
        pin = pya.Path(
            [pya.DPoint(0, -pin_length / 2), pya.DPoint(0, pin_length / 2)], bus_w / dbu
        )
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text(
            "opt1",
            pya.DTrans(
                pya.Trans.R0, min(bus_x) / dbu, (min(bus_y) + max(bus_y)) / 2 / dbu
            ),
        )
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = pya.DTrans(
            pya.Trans.R90, max(bus_x) / dbu, (min(bus_y) + max(bus_y)) / 2 / dbu
        )
        pin = pya.Path(
            [pya.DPoint(0, pin_length / 2), pya.DPoint(0, -pin_length / 2)], bus_w / dbu
        )
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = pya.Text(
            "opt2",
            pya.DTrans(
                pya.Trans.R90, max(bus_x) / dbu, (min(bus_y) + max(bus_y)) / 2 / dbu
            ),
        )
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Dev box
        # Encapsulate the pcell within a box for error checking
        w = self.w
        dev = pya.DBox(-(r + w), r + w + cg + bus_w + 0.5, r + w, -(r + w) - 0.5)
        shapes(LayerDevRecN).insert(dev)
