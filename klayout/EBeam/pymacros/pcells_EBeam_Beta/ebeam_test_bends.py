"""
Create a layout with band bends
uses: waveguide bend cutback structure

- this can be executed directly, or loaded by the technology library
- Waveguide types are loaded from the XML file
- Pitch of the waveguides is determined by the DevRec layer
- When executed directly, the unit test instantiates all the waveguide types

PCell options:
 - waveguide type
 - ports_opposite = True: input on left, output on right
                  = False: both i/o on left
by Lukas Chrostowski, 2024
"""

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class ebeam_test_bends(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        self.cellName = self.__class__.__name__
        super(eval(self.cellName), self).__init__()

        self.technology_name = "EBeam"

        from SiEPIC.utils import load_Waveguides_by_Tech

        self.TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Load all waveguides
        waveguide_types = load_Waveguides_by_Tech(self.technology_name)

        # Make a copy so that we don't modify the original definitions
        import copy

        self.waveguide_types = copy.deepcopy(waveguide_types)
        """
        # Debugging:
        print(id(waveguide_types))
        print(id(self.waveguide_types))
        """

        # downselect to non-compound types only.
        self.waveguide_types = [
            t for t in self.waveguide_types if "compound_waveguide" not in t
        ]

        # declare the parameters
        p = self.param(
            "waveguide_type",
            self.TypeList,
            "Waveguide Type",
            default=self.waveguide_types[0]["name"],
        )
        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])
        self.param(
            "override_width", self.TypeDouble, "Override waveguide width", default=0
        )
        self.param(
            "override_radius", self.TypeDouble, "Override waveguide radius", default=0
        )
        self.param(
            "override_bezier",
            self.TypeDouble,
            "Override waveguide Bezier parameter",
            default=0,
        )
        self.param("columns", self.TypeInt, "Number of columns", default=5)
        self.param("rows", self.TypeInt, "Number of double rows", default=5)
        #        self.param("tot_bends", self.TypeInt, "Total number of bends", default = 2, readonly=True)
        self.param(
            "tot_bends", self.TypeInt, "Total number of bends", default=2, readonly=True
        )

    def coerce_parameters_impl(self):
        #        if 'tot_bends1' in dir(self):
        #            self.tot_bends = self.tot_bends1 # self.columns * self.rows
        self.tot_bends = self.columns * 2 * 4 * self.rows + 2

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s_%s_override:%s_%s_%s" % (
            self.cellName,
            self.tot_bends,
            self.waveguide_type.replace(" ", "_"),
            self.override_width,
            self.override_radius,
            round(self.override_bezier, 3),
        )

    def get_waveguide_parameters(self):
        """
        Get the Waveguide Type from the PCell, and update waveguide parameters
        """
        from SiEPIC.utils import load_Waveguides_by_Tech

        # Load all waveguides
        waveguide_types = load_Waveguides_by_Tech(self.technology_name)
        # Make a copy so that we don't modify the original definitions
        import copy

        self.waveguide_types = copy.deepcopy(waveguide_types)

        self.waveguide_params = [
            t for t in self.waveguide_types if t["name"] == self.waveguide_type
        ]
        if not self.waveguide_params:
            raise Exception("Waveguides.XML not correctly configured")
        self.waveguide_params = self.waveguide_params[0]

        wg_params = self.waveguide_params

        if self.override_width > 0:
            delta_width = self.override_width - float(self.waveguide_params["width"])
            self.waveguide_params["width"] = str(self.override_width)
        else:
            delta_width = 0
        # Adjust all the width parameters
        for wg in wg_params["component"]:
            wg["width"] = str(float(wg["width"]) + delta_width)

        if self.override_radius > 0:
            self.waveguide_params["radius"] = str(self.override_radius)
        if self.override_bezier > 0:
            self.waveguide_params["bezier"] = str(self.override_bezier)

        # DevRec width
        if "DevRec" not in [wg["layer"] for wg in wg_params["component"]]:
            from SiEPIC import _globals

            self.devrec = (
                max([float(wg["width"]) for wg in wg_params["component"]])
                + _globals.WG_DEVREC_SPACE * 2
            )
        else:
            self.devrec = float(
                [f for f in wg_params["component"] if f["layer"] == "DevRec"][0][
                    "width"
                ]
            )

        # Radius
        self.radius = float(wg_params["radius"])

        # Waveguide pin width
        self.wg_width = float(wg_params["width"])

        """
        # Debugging:
        from SiEPIC.utils import load_Waveguides_by_Tech
        print(load_Waveguides_by_Tech(self.technology_name)[0] )
        print(id(load_Waveguides_by_Tech(self.technology_name)[0] ))
        print(self.waveguide_types[0])
        print(id(self.waveguide_types[0]))
        print(wg_params)     
        """

    def produce_impl(self):
        self.get_waveguide_parameters()
        devrec = self.devrec
        radius = self.radius

        if 0:
            # Spiral

            # SBend offset in the middle of the spiral
            if "sbends" in self.waveguide_params:
                # Use the Bezier S-Bend (more space efficient)
                # if sbends=True in Waveguide.xml
                offset = radius - devrec / 2
                extra = 0
            else:
                # Use 2 x 90 degree bends
                offset = radius
                extra = devrec

            # Ensure the length is sufficient
            self.minlength = 2 * radius
            length0 = max(self.minlength, self.length)

            # min loops
            self.loops = max(self.loops, 1)

            # spiral points
            points = [
                DPoint(-length0, offset),
                DPoint(0.0, offset),
                DPoint(0.0, -offset),
                DPoint(length0, -offset),
            ]
            for i in range(1, self.loops * 2, 2):
                points.insert(
                    0,
                    DPoint(
                        -length0 - devrec * (i - 1),
                        offset - radius * 2 - devrec * (i - 1) - extra,
                    ),
                )
                points.insert(
                    0,
                    DPoint(
                        length0 + devrec * i,
                        offset - radius * 2 - devrec * (i - 1) - extra,
                    ),
                )
                points.insert(
                    0,
                    DPoint(
                        length0 + devrec * i, -offset + radius * 2 + devrec * i + extra
                    ),
                )
                points.insert(
                    0,
                    DPoint(
                        -length0 - devrec * (i + 1),
                        -offset + radius * 2 + devrec * i + extra,
                    ),
                )
                points.append(
                    DPoint(
                        length0 + devrec * (i - 1),
                        radius * 2 - offset + devrec * (i - 1) + extra,
                    )
                )
                points.append(
                    DPoint(
                        -length0 - devrec * i,
                        radius * 2 - offset + devrec * (i - 1) + extra,
                    )
                )
                points.append(
                    DPoint(
                        -length0 - devrec * i, -radius * 2 + offset - devrec * i - extra
                    )
                )
                points.append(
                    DPoint(
                        length0 + devrec * (i + 1),
                        -radius * 2 + offset - devrec * i - extra,
                    )
                )
            if not self.ports_opposite:
                points.append(
                    DPoint(
                        length0 + devrec * (i + 1),
                        radius * 2 - offset + devrec * (i + 1) + extra,
                    )
                )
                points.append(
                    DPoint(
                        -length0 - devrec * (i + 1),
                        radius * 2 - offset + devrec * (i + 1) + extra,
                    )
                )
            points.pop(0)
            points.insert(
                0,
                DPoint(
                    -length0 - devrec * (i + 1),
                    -offset + radius * 2 + devrec * i + extra,
                ),
            )

        else:
            # bend test structure
            points = [DPoint(0, 0)]
            for j in range(0, self.rows):
                dy = radius * 4 * j
                for i in range(1, self.columns * 2 + 1, 2):
                    points.append(DPoint(radius * 2 * (i), dy))
                    points.append(DPoint(radius * 2 * (i), radius * 2 + dy))
                    points.append(DPoint(radius * 2 * (i + 1), radius * 2 + dy))
                    points.append(DPoint(radius * 2 * (i + 1), dy))
                points.append(DPoint(radius * 2 * (i + 2), dy))
                points.append(DPoint(radius * 2 * (i + 2), radius * 2 + dy))
                for i in range(self.columns * 2 - 1, 0, -2):
                    points.append(DPoint(radius * 2 * (i + 1), radius * 2 + dy))
                    points.append(DPoint(radius * 2 * (i + 1), radius * 4 + dy))
                    points.append(DPoint(radius * 2 * (i), radius * 4 + dy))
                    points.append(DPoint(radius * 2 * (i), radius * 2 + dy))
                points.pop(-1)
                points.pop(-1)
            #            points.append(DPoint(radius*2*(i+2),radius*2*self.rows))
            points.append(DPoint(0, radius * 4 * self.rows))
            self.tot_bends1 = len(points)
            print("Number of bends: %s" % self.tot_bends)

        # Create a path and waveguide
        path = DPath(points, 0.5)
        """
        # Debuggin, to make sure there are no duplicate vertices
        print(path.to_s())
        path = path.unique_points()
        print(path.to_s())
        """

        if 0:
            # This inserts a waveguide where the parameters are fixed from Waveguide.XML
            # using the Waveguide PCell
            self.layout.technology_name = (
                self.technology_name
            )  # required otherwise "create_cell" doesn't load
            pcell = self.layout.create_cell(
                "Waveguide",
                self.technology_name,
                {"path": path, "waveguide_type": self.waveguide_type},
            )
            t = Trans(Trans.R0, 0, 0)
            self.cell.insert(CellInstArray(pcell.cell_index(), t))
        else:
            # This inserts a waveguide where the parameters can be modified
            # using the function layout_waveguide3.
            from SiEPIC.utils.layout import layout_waveguide3

            # Make sure the technology name is associated with the layout
            #  PCells don't seem to know to whom they belong!
            if self.layout.technology_name == "":
                self.layout.technology_name = self.technology_name
            self.waveguide_params["waveguide_type"] = self.waveguide_type
            ipoints = [p.to_itype(self.layout.dbu) for p in points]

            waveguide_length = layout_waveguide3(
                self.cell, ipoints, self.waveguide_params, debug=False
            )
            print("done layout_waveguide3 test_bends")


# Save the path, used for loading WAVEGUIDES.XML
import os

filepath = os.path.dirname(os.path.realpath(__file__))


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("ebeam_test_bends", ebeam_test_bends())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: test bends")

    from SiEPIC.utils.layout import new_layout
    from SiEPIC.scripts import zoom_out

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)
    # floorplan(topcell, 100e3, 100e3)

    # instantiate the cell
    library = tech + "test_lib"

    # Create test structures for all the types of waveguides
    from SiEPIC.utils import load_Waveguides_by_Tech

    waveguide_types = load_Waveguides_by_Tech(tech)
    xmax = 0
    ports_opposite = False
    flatten = False
    y = 0
    x = xmax
    if 1:
        # only run the first type
        waveguide_types = [waveguide_types[0]]
    for wg in waveguide_types:
        pcell = ly.create_cell(
            "ebeam_test_bends",
            library,
            {
                "waveguide_type": wg["name"],
                "length": 100,
                "loops": 1,
                "flatten": flatten,
                "ports_opposite": ports_opposite,
            },
        )
        t = Trans(Trans.R0, x, y - pcell.bbox().bottom)
        inst = topcell.insert(CellInstArray(pcell.cell_index(), t))
        y += pcell.bbox().height() + 2000
        xmax = max(xmax, x + inst.bbox().width())

    zoom_out(topcell)
