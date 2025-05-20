"""
Create a layout with many utruns
uses: waveguide uturn cutback structure

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
from pya import CellInstArray, Trans, DTrans, Library, DPoint
from SiEPIC.utils import get_technology_by_name
from SiEPIC.scripts import connect_cell, connect_pins_with_waveguide
from SiEPIC.utils import load_Waveguides_by_Tech
from SiEPIC.utils.layout import new_layout, floorplan, make_pin
import os

class ebeam_test_uturn_euler(pya.PCellDeclarationHelper):
    def __init__(self):
        # Important: initialize the super class
        self.cellName = self.__class__.__name__
        super(eval(self.cellName), self).__init__()

        self.technology_name = "EBeam"
        self.TECHNOLOGY = get_technology_by_name(self.technology_name)

        # Load all waveguides
        waveguide_types = load_Waveguides_by_Tech(self.technology_name)
        import copy          # Make a copy so that we don't modify the original definitions
        self.waveguide_types = copy.deepcopy(waveguide_types)
        # downselect to non-compound types only.
        self.waveguide_types = [
            t for t in self.waveguide_types if "compound_waveguide" not in t
        ]

        # declare the parameters
        p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default=self.waveguide_types[0]["name"])
        for wa in self.waveguide_types:
            p.add_choice(wa["name"], wa["name"])
        #self.param("override_width", self.TypeDouble, "Override waveguide width", default=0 )
        #self.param("override_radius", self.TypeDouble, "Override waveguide radius", default=0)
        #self.param("override_bezier", self.TypeDouble, "Override waveguide Bezier parameter", default=0)
        self.param("columns", self.TypeInt, "Number of columns", default=5)
        self.param("rows", self.TypeInt, "Number of double rows", default=5)
        self.param("radius", self.TypeDouble, "Radius", default=5)
        self.param("p", self.TypeDouble, "Euler parameter", default=0.25)
        self.param("tot_bends", self.TypeInt, "Total number of bends", default=2, hidden=True)

    def coerce_parameters_impl(self):
        self.tot_bends = self.columns * 2 * self.rows
        # print(f'coerce: tot bends {self.tot_bends}')

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "%s_%s_%s_%s_%s" % (
            self.cellName,
            self.tot_bends,
            self.waveguide_type.replace(" ", "_"),
            self.p,
            self.radius,
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
        '''
        if self.override_width > 0:
            delta_width = self.override_width - float(self.waveguide_params["width"])
            self.waveguide_params["width"] = str(self.override_width)
        else:
            delta_width = 0
        '''
        delta_width = 0
        
        # Adjust all the width parameters
        for wg in wg_params["component"]:
            wg["width"] = str(float(wg["width"]) + delta_width)

        '''
        if self.override_radius > 0:
            self.waveguide_params["radius"] = str(self.override_radius)
        if self.override_bezier > 0:
            self.waveguide_params["bezier"] = str(self.override_bezier)
        '''
        
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
        # self.radius = float(wg_params["radius"])

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
        dbu = self.layout.dbu
        radius = self.radius

        self.layout.technology_name = (self.technology_name)  # required otherwise "create_cell" doesn't load
        pcell = self.layout.create_cell(
            "euler_bend_180", 'EBeam_Beta',
            {"radius": radius, "p": self.p, "ww": self.wg_width},
        )

        # t = Trans(Trans.R90, 0, 0)
        # self.cell.insert(CellInstArray(pcell.cell_index(), t))

        inst_u_left_up = []
        inst_u_left_down = []
        inst_u_right_up  = []
        inst_u_right_down = []

        # bend test structure
        points = [DPoint(0, 0)]
        for j in range(0, self.rows):
            dy = radius * 4 * j
            for i in range(1, self.columns * 2 + 1, 2):
                inst_u_down = self.cell.insert(CellInstArray(pcell.cell_index(), Trans(Trans.R90, radius * 2 * (i + j%2)/dbu, (dy)/dbu)))
                if i == 1:
                    inst_u_left_down.append (inst_u_down)
            inst_u_right_down.append(inst_u_down)
            for i in range(1, self.columns * 2 + 1, 2):
                inst_u_up = self.cell.insert(CellInstArray(pcell.cell_index(), Trans(Trans.R270, radius * 2 * (i - j%2)/dbu, (dy)/dbu)))
                if i == 1:
                    inst_u_left_up.append(inst_u_up)
            inst_u_right_up.append(inst_u_up)
            
        for j in range(0, self.rows-1, 2):
            inst_wg = connect_pins_with_waveguide(inst_u_right_up[j], 'opt2', inst_u_right_down[j+1], 'opt1', waveguide_type=self.waveguide_type)
            if j < (self.rows-2):
                inst_wg = connect_pins_with_waveguide(inst_u_left_up[j+1], 'opt1', inst_u_left_down[j+2], 'opt2', waveguide_type=self.waveguide_type)

        # Make pins, so we can connect a waveguide to it
        make_pin(self.cell,"opt_input",inst_u_left_down[0].pinPoint('opt2'),self.wg_width,self.TECHNOLOGY['PinRec'],270)
        make_pin(self.cell,"opt_output",inst_u_left_up[-1].pinPoint('opt1'),self.wg_width,self.TECHNOLOGY['PinRec'],90)

        print("Number of u-turns: %s" % self.tot_bends)
        # self.cell.set_property('tot_bends',str(self.tot_bends))
        # self.layout.set_property('tot_bends',str(self.tot_bends))

        text = pya.Text(
            f'Number of u-turns={self.tot_bends}', pya.Trans(pya.Trans.R0, 0, 0), 3e3, -1)
        self.cell.shapes(self.TECHNOLOGY["Text"]).insert(text)

class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("ebeam_test_uturn_euler", ebeam_test_uturn_euler())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: test bends")

    from SiEPIC.utils.layout import new_layout
    from SiEPIC.scripts import zoom_out
    
    import siepic_ebeam_pdk

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)
    floorplan(topcell, 605e3, 410e3)
    dbu = ly.dbu

    # instantiate the cell
    library = tech + "test_lib"

    # Create test structures for all the types of waveguides
    waveguide_types = load_Waveguides_by_Tech(tech)
    
    xmax = 0
    y = 0
    x = xmax
    if 1:
        # only run the first type
        waveguide_type = waveguide_types[0]
        waveguide_types = [waveguide_type]

    # Import the grating coupler from the SiEPIC EBeam Library
    cell_ebeam_gc = ly.create_cell("GC_TE_1550_8degOxide_BB", "EBeam")
    x = -cell_ebeam_gc.bbox().left
    y = -cell_ebeam_gc.bbox().bottom
    inst_GC1 = topcell.insert(CellInstArray(cell_ebeam_gc.cell_index(), 
                    Trans(Trans.R0, x, y)))
    t_gc = Trans(Trans.R0, x, y + 127/dbu)
    inst_GC2 = topcell.insert(CellInstArray(cell_ebeam_gc.cell_index(), 
                    t_gc))

    # Add the u-turn
    print(waveguide_type)
    columns = 13
    rows = 10
    radius = 10
    p = 0.25
    '''
    columns = 27
    rows = 20
    radius = 5
    '''
    pcell = ly.create_cell(
        "ebeam_test_uturn_euler",
        library,
        {
            "waveguide_type": waveguide_type["name"],
            "columns": columns,
            "rows": rows,
            "radius": radius,
            "p": p,
            "tot_bends": 2 * columns * rows,
        },
    )

    t = Trans(Trans.R0, inst_GC1.pinPoint('opt1').x+15/dbu, inst_GC1.pinPoint('opt1').y+0/dbu)
    inst = topcell.insert(CellInstArray(pcell.cell_index(), t))
    y += pcell.bbox().height() + 2000
    xmax = max(xmax, x + inst.bbox().width())

    # testing label
    '''
    # Asking how to query calculated PCell parameters:
    # https://www.klayout.de/forum/discussion/2720/querying-pcells-for-calculated-parameters/p1?new=1
    print(dir(inst))
    params1 = pcell.pcell_parameters()
    params2 = inst.pcell_parameters()
    print(f"  has params: {params1}, {params2}")
    '''
    tot_bends = inst.pcell_parameter('tot_bends')
    text = pya.Text (f'opt_in_TE_1550_device_uturnEuler{tot_bends}', t_gc)
    TECHNOLOGY = get_technology_by_name(tech)
    topcell.shapes(TECHNOLOGY["Text"]).insert(text)
    
    # waveguide connections
    connect_pins_with_waveguide(inst_GC1, 'opt1', inst, 'opt_input', waveguide_type=waveguide_type["name"], turtle_B=[5,-90,10,-90,5,90])
    connect_pins_with_waveguide(inst_GC2, 'opt1', inst, 'opt_output', waveguide_type=waveguide_type["name"], turtle_B=[5,90,10,90], turtle_A=[5,90])

    topcell.show(os.path.dirname(__file__))
