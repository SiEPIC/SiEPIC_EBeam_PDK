"""
Create a layout of a paperclip spiral,
uses: delay line, waveguide loss cutback structure

- this can be executed directly, or loaded by the technology library
- you can resize the PCell by using the Partial select tool "L", and moving
   the GUIDING SHAPE Box
- Waveguide types are loaded from the XML file
- Pitch of the waveguides is determined by the DevRec layer
- When executed directly, the unit test instantiates all the waveguide types

PCell options:
 - waveguide type
 - ports_opposite = True: input on left, output on right
                  = False: both i/o on left
by Lukas Chrostowski, 2023-2024
"""

import pya
from pya import *
from SiEPIC.utils import get_technology_by_name
from pya import DPoint

class spiral_paperclip(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        self.cellName = self.__class__.__name__
        super(eval(self.cellName), self).__init__()

        self.technology_name = "EBeam"

        from SiEPIC.utils import load_Waveguides_by_Tech

        self.TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Load all strip waveguides
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)

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
            "ports_opposite",
            self.TypeBoolean,
            "Waveguide ports on opposite sides",
            default=False,
        )
        self.param(
            "port_vertical",
            self.TypeBoolean,
            "One waveguide port pointing vertically",
            default=False,
        )
        self.param("loops", self.TypeInt, "Number of loops", default=2)
        self.minlength = 2 * float(self.waveguide_types[0]["radius"])
        self.param(
            "length",
            self.TypeDouble,
            "Inner length (min 2 x bend radius)",
            default=self.minlength,
        )
        self.param(
            "box",
            self.TypeShape,
            "Box",
            default=pya.DBox(
                -self.minlength, -self.minlength / 2, self.minlength, self.minlength / 2
            ),
        )
        self.param(
            "length1",
            self.TypeDouble,
            "length: for PCell",
            default=self.minlength,
            hidden=True,
        )
        self.param(
            "flatten",
            self.TypeBoolean,
            "Flatten the PCell, for scripting",
            default=False,
        )
        self.param(
            "tot_length",
            self.TypeDouble,
            "Total length estimate (mm)",
            default=0,
            readonly=True,
        )

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s_%s_%s" % (
            self.cellName,
            self.loops,
            self.length,
            self.waveguide_type.replace(" ", "_"),
        )

    def get_waveguide_parameters(self):
        """
        Get the Waveguide Type from the PCell, and update waveguide parameters
        """
        self.waveguide_params = [
            t for t in self.waveguide_types if t["name"] == self.waveguide_type
        ]
        if not self.waveguide_params:
            raise Exception("Waveguides.XML not correctly configured")
        self.waveguide_params = self.waveguide_params[0]
        wg_params = self.waveguide_params
        wg_params2 = wg_params

        # check for compound type
        if "compound_waveguide" in wg_params:
            sm_wg = self.waveguide_params["compound_waveguide"]["singlemode"]
            mm_wg = self.waveguide_params["compound_waveguide"]["multimode"]
            wg_params = [t for t in self.waveguide_types if t["name"] == sm_wg][0]
            wg_params2 = [t for t in self.waveguide_types if t["name"] == mm_wg][0]

        # DevRec width
        if "DevRec" not in [wg["layer"] for wg in wg_params2["component"]]:
            from SiEPIC import _globals

            self.devrec = (
                max([float(wg["width"]) for wg in wg_params2["component"]])
                + _globals.WG_DEVREC_SPACE * 2
            )
        else:
            self.devrec = float(
                [f for f in wg_params2["component"] if f["layer"] == "DevRec"][0][
                    "width"
                ]
            )

        # Radius
        self.radius = float(wg_params["radius"])

        # Waveguide pin width
        self.wg_width = float(wg_params["width"])

    def coerce_parameters_impl(self):
        self.get_waveguide_parameters()

        # We employ coerce_parameters_impl to decide whether the handle or the
        # numeric parameters have changed. We update the
        # numerical value or the shape, depending on which on has not changed.
        w = None
        if isinstance(self.box, pya.Box):
            w = self.box.right * self.layout.dbu
            # print('%s Box: width %s ' %(self.cellName,w))
        if isinstance(self.box, pya.DBox):
            w = self.box.right
            # print('%s DBox: width %s ' %(self.cellName,w))
        if w != None and abs(self.length1 - self.length) < 1e-6:
            if w < self.minlength:
                w = self.minlength
            # print('%s update from GUI Box: %s ' %(self.cellName,w))
            self.length = w
            self.length1 = w
        else:
            # print('%s update from PCell parameters: %s ' %(self.cellName,self.length1))
            self.length1 = self.length
        self.box = pya.DBox(
            -self.length, -self.minlength / 2, self.length, self.minlength / 2
        )

        # estimate length
        # estimate total length of the spiral
        length0 = max(self.minlength, self.length)
        devrec = self.devrec
        radius = self.radius

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

        # min loops
        self.loops = max(self.loops, 1)

        # Calculate the points again to estimate the total length of the spiral using .distance pya method
        points = [
            DPoint(-length0, radius),
            DPoint(0.0, radius),
            DPoint(0.0, -radius),
            DPoint(length0, -radius),
        ]
        for i in range(1, self.loops * 2, 2):
            points.insert(
                0,
                DPoint(
                    -length0 - devrec * (i - 1), radius - radius * 2 - devrec * (i - 1)
                ),
            )
            points.insert(
                0, DPoint(length0 + devrec * i, radius - radius * 2 - devrec * (i - 1))
            )
            points.insert(
                0, DPoint(length0 + devrec * i, -radius + radius * 2 + devrec * i)
            )
            points.insert(
                0,
                DPoint(-length0 - devrec * (i + 1), -radius + radius * 2 + devrec * i),
            )
            points.append(
                DPoint(
                    length0 + devrec * (i - 1), radius * 2 - radius + devrec * (i - 1)
                )
            )
            points.append(
                DPoint(-length0 - devrec * i, radius * 2 - radius + devrec * (i - 1))
            )
            points.append(
                DPoint(-length0 - devrec * i, -radius * 2 + radius - devrec * i)
            )
            points.append(
                DPoint(length0 + devrec * (i + 1), -radius * 2 + radius - devrec * i)
            )
        if not self.ports_opposite:
            points.append(
                DPoint(
                    length0 + devrec * (i + 1), radius * 2 - radius + devrec * (i + 1)
                )
            )
            points.append(
                DPoint(
                    -length0 - devrec * (i + 1), radius * 2 - radius + devrec * (i + 1)
                )
            )
        points.pop(0)
        points.insert(
            0, DPoint(-length0 - devrec * (i + 1), -radius + radius * 2 + devrec * i)
        )

        for j in range(1, len(points)):
            self.tot_length += points[j - 1].distance(points[j])

        # Update the total length parameter
        self.tot_length = self.tot_length / 1000  # Convert to mm

        # self.tot_length = self.length*2 * (2* self.loops+1+ 0 if self.ports_opposite else 1 )/ 1000 # micron to mm.

    def can_create_from_shape_impl(self):
        return self.shape.is_box()

    def transformation_from_shape_impl(self):
        # Implement the "Create PCell from shape" protocol: we use the center of the shape's
        # bounding box to determine the transformation
        return pya.Trans(self.shape.bbox().center())

    def parameters_from_shape_impl(self):
        # self.path = self.shape.path
        # Implement the "Create PCell from shape" protocol: we set r and l from the shape's
        # bounding box width and layer
        self.width = self.shape.bbox().width() * self.layout.dbu
        self.height = self.shape.bbox().height() * self.layout.dbu

    def produce_impl(self):
        self.get_waveguide_parameters()
        devrec = self.devrec
        radius = self.radius

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
            DPoint(-length0+radius*2, offset),
            DPoint(-length0+radius*2, -offset),
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
                    length0 + devrec * i, offset - radius * 2 - devrec * (i - 1) - extra
                ),
            )
            points.insert(
                0,
                DPoint(length0 + devrec * i, -offset + radius * 2 + devrec * i + extra),
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
                DPoint(-length0 - devrec * i, 
                       -radius * 2 + offset - devrec * i - extra)
            )
            points.append(
                DPoint(
                    length0 + devrec * (i + 1),
                    -radius * 2 + offset - devrec * i - extra,
                )
            )
        if self.port_vertical:
            points.pop(-1)
            points.pop(-1)
            points.append(
                DPoint(-length0 - devrec * i, 
                       radius - offset + devrec * (i - 1) + extra)
            )
        if not self.ports_opposite and not self.port_vertical:
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
                -length0 - devrec * (i + 1), -offset + radius * 2 + devrec * i + extra
            ),
        )

        # Create a path and waveguide
        path = DPath(points, 0.5)
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

        # If the waveguide is a Compound type:
        # Flatten the PCell and remove the DevRec and PinRec layers
        if "compound_waveguide" in self.waveguide_params and self.flatten:
            self.cell.flatten(True)
            LayerPinRecN = self.layout.layer(self.TECHNOLOGY["PinRec"])
            LayerDevRecN = self.layout.layer(self.TECHNOLOGY["DevRec"])
            self.cell.clear(LayerPinRecN)
            self.cell.clear(LayerDevRecN)
            self.cell.clear(self.layout.layer(self.TECHNOLOGY["Waveguide"]))
            devrec_box = self.cell.bbox()
            if self.port_vertical:
                devrec_box = (pya.Region(devrec_box) - pya.Region(pya.DBox(
                    -length0 - devrec * (i+1), 
                    radius - offset + devrec * (i - 1) + extra, 
                    -length0 - devrec * (i-0.5), 
                    -radius * 2 + offset - devrec * (i+3) - extra).to_itype(self.layout.dbu))).merged()
            self.cell.shapes(LayerDevRecN).insert(devrec_box)

            # Create the pins on the input & output waveguides
            from SiEPIC.utils.layout import make_pin

            if self.port_vertical:
                make_pin(
                    self.cell,
                    "optA",
                    [
                        -length0 - devrec * (i),
                        radius - offset + devrec * (i - 1) + extra,
                    ],
                    self.wg_width,
                    LayerPinRecN,
                    270,
                )
            else:
                if self.ports_opposite:
                    make_pin(
                        self.cell,
                        "optA",
                        [
                            length0 + devrec * (i + 1),
                            -radius * 2 + offset - devrec * i - extra,
                        ],
                        self.wg_width,
                        LayerPinRecN,
                        0,
                    )
                else:
                    make_pin(
                        self.cell,
                        "optA",
                        [
                            -length0 - devrec * (i + 1),
                            radius * 2 - offset + devrec * (i + 1) + extra,
                        ],
                        self.wg_width,
                        LayerPinRecN,
                        180,
                    )
            make_pin(
                self.cell,
                "optB",
                [
                    -length0 - devrec * (i + 1),
                    -offset + radius * 2 + devrec * i + extra,
                ],
                self.wg_width,
                LayerPinRecN,
                180,
            )


# Save the path, used for loading WAVEGUIDES.XML
import os

filepath = os.path.dirname(os.path.realpath(__file__))


class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("spiral_paperclip", spiral_paperclip())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: Spiral Paperclip")

    from SiEPIC.utils.layout import new_layout
    from SiEPIC.scripts import zoom_out

    from SiEPIC._globals import Python_Env
    if Python_Env == 'Script':
        # For external Python mode, when installed using pip install siepic_ebeam_pdk
        import siepic_ebeam_pdk

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)
    # floorplan(topcell, 100e3, 100e3)

    # instantiate the cell
    library = tech + "test_lib"

    if 0:
        # default waveguide
        pcell = ly.create_cell("spiral_paperclip", library, {})
        t = Trans(Trans.R0, 0, 0)
        topcell.insert(CellInstArray(pcell.cell_index(), t))

        # multimode
        pcell = ly.create_cell(
            "spiral_paperclip",
            library,
            {
                "waveguide_type": "Si routing TE 1550 nm (compound waveguide)",
                "length": 100,
                "loops": 1,
            },
        )
        t = Trans(Trans.R0, 0, 40000)
        topcell.insert(CellInstArray(pcell.cell_index(), t))

    # Create spirals for all the types of waveguides
    from SiEPIC.utils import load_Waveguides_by_Tech

    waveguide_types = load_Waveguides_by_Tech(tech)

    # test vertical waveguide
    pcell = ly.create_cell(
        "spiral_paperclip",
        library,
        {
            "waveguide_type": waveguide_types[-1]["name"],
            "length": 100,
            "loops": 1,
            "flatten": True,
            "port_vertical": True,
        },
    )
    t = Trans(Trans.R0, -pcell.bbox().width(), 0)
    inst = topcell.insert(CellInstArray(pcell.cell_index(), t))

    # loop through many permutations
    xmax = 0
    for ports_opposite in [True, False]:
        for flatten in [True, False]:
            y = 0
            x = xmax
            for wg in waveguide_types:
                # print(wg)
                pcell = ly.create_cell(
                    "spiral_paperclip",
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


    # Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
    if Python_Env == 'Script':
        from SiEPIC.scripts import export_layout
        path = os.path.dirname(os.path.realpath(__file__))
        file_out = export_layout (topcell, path, filename='spiral_paperclip', relative_path='', format='oas')
        from SiEPIC.utils import klive
        klive.show(file_out, technology=tech)
