import os
from pya import (
    PCellDeclarationHelper,
    Point,
    DPoint,
    Path,
    Polygon,
    Text,
    Box,
    LayerInfo,
    Trans,
    CellInstArray,
    Library,
)
from math import pi, acos, sqrt
from SiEPIC.extend import to_itype
from SiEPIC.utils import arc_wg_xy, get_technology_by_name
from SiEPIC.utils.layout import new_layout
from SiEPIC.scripts import zoom_out
from SiEPIC._globals import PIN_LENGTH as pin_length, Python_Env


class strip_to_slot(PCellDeclarationHelper):
    """
    The PCell declaration for the strip_to_slot.
    draft by Lukas Chrostowski july 24, 2017
    Modified by Alexander Tofini march 17, 2021
    based on https://www.osapublishing.org/oe/fulltext.cfm?uri=oe-21-16-19029&id=259920

    updated by Lukas Chrostowski, 2021/12
      - reduce the curved waveguide section, longer device for lower loss
      - simulated using EME to give 99% efficiency

    updated by Mustafa Hammood, 2025/02
      - refactored redundant code, added in-cell execution
      - added optional theta for slot curve (via *radius*)
    """

    def __init__(self):
        super(strip_to_slot, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")
        # declare parameters
        self.param("silayer", self.TypeLayer, "Si Layer", default=TECHNOLOGY["Si"])
        self.param("r", self.TypeDouble, "Radius", default=15)
        self.param("w", self.TypeDouble, "Waveguide Width", default=0.5)
        self.param("rails", self.TypeDouble, "Rails", default=0.25)
        self.param("slot", self.TypeDouble, "Slot", default=0.1)
        self.param("taper", self.TypeDouble, "Taper Length", default=15.0)
        self.param("wt", self.TypeDouble, "Terminated Curved Width", default=0.1)
        self.param(
            "offset", self.TypeDouble, "Ending Offset for Curved section", default=1.0
        )
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=LayerInfo(10, 0))

    def display_text_impl(self):
        return (
            "Strip_To_Slot(rails="
            + ("%.3f" % self.rails)
            + ", slot="
            + ("%g" % self.slot)
            + ")"
        )

    def can_create_from_shape_impl(self):
        return False

    def produce_impl(self):

        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSiN = ly.layer(self.silayer)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)

        # Convert parameters to internal units
        w = to_itype(self.w, dbu)
        r = to_itype(self.r, dbu)
        slot = to_itype(self.slot, dbu)
        rails = to_itype(self.rails, dbu)
        taper = to_itype(self.taper, dbu)
        wt = to_itype(self.wt, dbu)
        offset = to_itype(self.offset, dbu)

        # Draw the **curved arc** for the slot converter
        x = 0
        y = r + rails / 2 + w + slot
        theta = (acos((r - offset) / r) / (2 * pi)) * 360
        arc_width = sqrt(r**2 - (r - offset) ** 2)
        self.cell.shapes(LayerSiN).insert(
            arc_wg_xy(x, y, r + rails / 2 - wt / 2, wt, 270, 270 + theta)
        )

        # **Taper polygon**
        pts = [
            Point.from_dpoint(DPoint(0, w)),
            Point.from_dpoint(DPoint(0, 0)),
            Point.from_dpoint(DPoint(-taper, w - rails)),
            Point.from_dpoint(DPoint(-taper, w)),
        ]
        shapes(LayerSiN).insert(Polygon(pts))

        # **Top left half waveguide** (slot side)
        wg1 = Polygon(
            [
                Point.from_dpoint(DPoint(-taper, w + slot)),
                Point.from_dpoint(DPoint(-taper, w + slot + rails)),
                Point.from_dpoint(DPoint(0, w + slot + wt)),
                Point.from_dpoint(DPoint(0, w + slot)),
            ]
        )
        shapes(LayerSiN).insert(wg1)

        # **Bus waveguide**
        wg2 = Box(0, 0, arc_width + wt, w)
        shapes(LayerSiN).insert(wg2)

        # **Pins**
        pin_path1 = Path(
            [
                Point(-taper + pin_length, w + slot / 2),
                Point(-taper - pin_length, w + slot / 2),
            ],
            2 * rails + slot,
        )
        shapes(LayerPinRecN).insert(pin_path1)
        text1 = Text("opt1", Trans(Trans.R0, -taper, w))
        text1.text_size = 0.5 / dbu
        shapes(LayerPinRecN).insert(text1)

        pin_path2 = Path(
            [
                Point(arc_width + wt - pin_length, w / 2),
                Point(arc_width + wt + pin_length, w / 2),
            ],
            w,
        )
        shapes(LayerPinRecN).insert(pin_path2)
        text2 = Text("opt2", Trans(Trans.R0, arc_width + wt, w / 2))
        text2.text_size = 0.5 / dbu
        shapes(LayerPinRecN).insert(text2)

        # **Device recognition layer**
        dev = Box(-taper, -w / 2 - w, arc_width + wt, y - r + offset)
        shapes(LayerDevRecN).insert(dev)


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("strip_to_slot", strip_to_slot())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: Strip to Slot")

    if Python_Env == "Script":
        # For external Python mode, when installed using pip install siepic_ebeam_pdk
        import siepic_ebeam_pdk

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Create a strip_to_slot PCell
    pcell = ly.create_cell("strip_to_slot", library, {})
    t = Trans(Trans.R0, 0, 0)
    topcell.insert(CellInstArray(pcell.cell_index(), t))

    # Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
    if Python_Env == "Script":
        from SiEPIC.scripts import export_layout

        path = os.path.dirname(os.path.realpath(__file__))
        file_out = export_layout(
            topcell, path, filename="strip_to_slot", relative_path="", format="oas"
        )
        from SiEPIC.utils import klive

        klive.show(file_out, technology=tech)
