import pya
from pya import DPolygon, DPoint, DBox, DTrans, CellInstArray, Trans, Library
import os
# from pya import *
from SiEPIC.utils import get_technology_by_name


class PWB_edge_coupler(pya.PCellDeclarationHelper):
    """
    The PCell declaration for the photonic wirebond edge taper

    based on Becky Lin's 
    Author: Becky Lin SiEPIC_EBeam_PDK ebeam_PWB_surface_taper cell

    by Lukas Chrostowski, 2025
    
    Waveguide choices are loaded from WAVEGUIDES.xml
     - determiners the layer/material
     - reads the waveguide width, for the port
     - The taper is constructed using a single layer.
     - does not work for compound waveguides.
        
    """

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
        p = self.param("waveguide_type", self.TypeList, "Waveguide Type", default=self.waveguide_types[0]["name"])
        for wa in self.waveguide_types:
            if not "compound_waveguide" in wa:
                p.add_choice(wa["name"], wa["name"])

        # Taper
        self.param("taper_tip_width", self.TypeDouble, "Width of taper tip (microns)", default=0.13)
        #self.param("edge_offset", self.TypeDouble, "tip to edge gap (microns), negative extends past the etch", default=-10)
        self.param("taper_length", self.TypeDouble, "Waveguide taper length (microns)", default=100)
        self.param("taper_extension", self.TypeDouble, "Extension (straight) of the taper tip (microns)", default=10)

        # Alignment marker
        self.param("offset_align_tip", self.TypeDouble, "Alignment marker: offset from taper tip (microns)", default=10)
        self.param("pitch_align", self.TypeDouble, "Alignment marker: pitch of the two markers (microns)", default=50)

        # Trench
        self.param("trench_width", self.TypeDouble, "Trench width (microns)", default=100)
        self.param("trench_height", self.TypeDouble, "Trench height (microns)", default=50)
        self.param("layer_deep_etch", self.TypeLayer, "Trench layer", default=self.TECHNOLOGY["Deep Trench"])

        self.param("include_DevRec", self.TypeBoolean, "Draw the DevRec layer?", default=True)

        

    def get_waveguide_parameters(self):
        """
        Get the Waveguide Type from the PCell, and update waveguide parameters
        """

        from SiEPIC.utils import load_Waveguides_by_Tech
        # Load all waveguides
        self.TECHNOLOGY = get_technology_by_name(self.technology_name)
        self.waveguide_types = load_Waveguides_by_Tech(self.technology_name)
        # print(self.waveguide_types)

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
        
        # Waveguide layer / material
        wg_layers = ['Si', 'SiN']
        for w in wg_layers:
            if any([f for f in wg_params2["component"] if f["layer"] == w]):
                self.waveguide_layer = w


    def produce_impl(self):

        # Cell origin is the waveguide port
        
        self.get_waveguide_parameters()
        wg_width = self.wg_width
        self.waveguide_layer

        # define the taper
        pts = [
            DPoint(-self.taper_length, -self.taper_tip_width/2),
            DPoint(-self.taper_length-self.taper_extension, -self.taper_tip_width/2),
            DPoint(-self.taper_length-self.taper_extension, self.taper_tip_width/2),
            DPoint(-self.taper_length, self.taper_tip_width/2),
            DPoint(0, self.wg_width/2),
            DPoint(0, -self.wg_width/2),
        ]
        # place the taper
        layer = self.layout.layer(self.TECHNOLOGY[self.waveguide_layer])
        self.cell.shapes(layer).insert(DPolygon(pts))

        # Create the pins on the input waveguide
        from SiEPIC.utils.layout import make_pin
        make_pin(
            self.cell,
            "optA",
            [0, 0],
            self.wg_width,
            self.layout.layer(self.TECHNOLOGY["PinRec"]),
            0,
        )
        
        # draw alignment marker
        pts = [
            DPoint(0, 12.4 ),
            DPoint(0, 9 ),
            DPoint(3.5, 9 ),
            DPoint(3.5, 12.5 ),
            DPoint(0.1, 12.5 ),
            DPoint(0, 12.6 ),
            DPoint(0, 16 ),
            DPoint(-3.5, 16 ),
            DPoint(-3.5, 12.5 ),
            DPoint(-0.1, 12.5 ),
        ]

        # place alignment markers
        self.cell.shapes(layer).insert(DPolygon(pts).transformed(DTrans(DTrans.R0, -self.taper_length+self.offset_align_tip,0)))
        self.cell.shapes(layer).insert(DPolygon(pts).transformed(DTrans(DTrans.R0, -self.taper_length+self.pitch_align,0)))
 
        # Trench layer
        if self.layer_deep_etch:
            box_trench = DBox (-self.taper_length, 
                               -self.trench_height/2, 
                               -self.taper_length-self.trench_width, 
                               self.trench_height/2)
            layer = self.layout.layer(self.layer_deep_etch)
            self.cell.shapes(layer).insert(box_trench)
                    
        # DevRec
        if self.include_DevRec:
            box = DBox (-self.taper_length-self.taper_extension, -17, 0, 17)
            layer = self.layout.layer(self.TECHNOLOGY['DevRec'])
            if self.layer_deep_etch:
                dbu = self.layout.dbu
                box = pya.Region(box.to_itype(dbu)) + pya.Region(box_trench.to_itype(dbu))
                box.merge()
            self.cell.shapes(layer).insert(box)

class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = "test_lib"
        self.technology = tech
        self.layout().register_pcell("PWB_edge_coupler", PWB_edge_coupler())
        self.register(library)


if __name__ == "__main__":
    print("Test layout for: PWB_edge_coupler")

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
    library = "test_lib"

    # Create spirals for all the types of waveguides
    from SiEPIC.utils import load_Waveguides_by_Tech

    waveguide_types = load_Waveguides_by_Tech(tech)

    y = 0
    pcell = ly.create_cell(
        "PWB_edge_coupler",
        library,
        {
            "waveguide_type": waveguide_types[-1]["name"],
            "include_DevRec":True
        },
    )
    t = Trans(Trans.R0, -pcell.bbox().width(), y)
    inst = topcell.insert(CellInstArray(pcell.cell_index(), t))
    y += pcell.bbox().height() + 10e3
    
    pcell = ly.create_cell(
        "PWB_edge_coupler",
        library,
        {
            "waveguide_type": waveguide_types[-1]["name"],
            "include_DevRec":False
        },
    )
    t = Trans(Trans.R0, -pcell.bbox().width(), y)
    inst = topcell.insert(CellInstArray(pcell.cell_index(), t))
    y += pcell.bbox().height() + 10e3

    pcell = ly.create_cell(
        "PWB_edge_coupler",
        library,
        {
            "waveguide_type": waveguide_types[-1]["name"],
            "layer_deep_etch":None,
            "include_DevRec":True,
        },
    )
    t = Trans(Trans.R0, -pcell.bbox().width(), y)
    inst = topcell.insert(CellInstArray(pcell.cell_index(), t))

    topcell.show()

    # # Display the layout in KLayout, using KLayout Package "klive", which needs to be installed in the KLayout Application
    # if Python_Env == 'Script':
    #     from SiEPIC.scripts import export_layout
    #     path = os.path.dirname(os.path.realpath(__file__))
    #     file_out = export_layout (topcell, path, filename='PWB_edge_coupler', relative_path='', format='oas')
    #     from SiEPIC.utils import klive
    #     klive.show(file_out, technology=tech)
