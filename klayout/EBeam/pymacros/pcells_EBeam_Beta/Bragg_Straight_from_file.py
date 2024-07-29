import pya
from pya import *
from SiEPIC.utils import get_technology_by_name


class Bragg_Straight_from_file(pya.PCellDeclarationHelper):
    """
    by Rui Cheng 2020, UBC; modified by Lukas Chrostowski
    Description: Load Bragg grating waveguide vertices from a TXT file and draw

    Input: file with the format: (x1,y1,x2,y2;...)
    which can be generated in Matlab by:
      co = co / dbu;
      fid=fopen(file,'w');
      fprintf(fid,'(');
      fprintf(fid,'%d,%d;',round(co));
      fprintf(fid,')');
      fclose(fid);

    """

    def __init__(self):
        # Important: initialize the super class
        super(Bragg_Straight_from_file, self).__init__()
        TECHNOLOGY = get_technology_by_name("EBeam")

        # declare the parameters
        self.param("forder", self.TypeString, "Forder", default="")
        self.param("name", self.TypeString, "Name", default="Square_BP_B3.5_N2536_DW6")
        self.param("filetype", self.TypeString, "File type (txt)", default="txt")
        self.param("layer", self.TypeLayer, "Layer", default=TECHNOLOGY["Si"])
        self.param("port_w", self.TypeDouble, "Port Waveguide width", default=0.5)
        self.param(
            "pinrec", self.TypeLayer, "PinRec Layer", default=TECHNOLOGY["PinRec"]
        )
        self.param(
            "devrec", self.TypeLayer, "DevRec Layer", default=TECHNOLOGY["DevRec"]
        )
        self.param("textl", self.TypeLayer, "Text Layer", default=TECHNOLOGY["Text"])

    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "Bragg_Straight_from_file_%s" % (self.name)

    def coerce_parameters_impl(self):
        pass

    def can_create_from_shape(self, layout, shape, layer):
        return False

    def produce_impl(self):
        import os
        from SiEPIC.extend import to_itype

        # fetch the parameters
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes

        LayerSi = self.layer
        LayerSiN = ly.layer(LayerSi)
        LayerPinRecN = ly.layer(self.pinrec)
        LayerDevRecN = ly.layer(self.devrec)
        TextLayerN = ly.layer(self.textl)
        LayerPinRec = ly.layer(self.pinrec)

        file_path = os.path.join(self.forder, self.name + "." + self.filetype)
        # print('Bragg_Straight_from_file: input file: ' + file_path)

        if not (os.path.isfile(file_path)):
            error = "File not found: " + file_path
            text = Text(error, Trans(0, 0))
            shape = shapes(TextLayerN).insert(text)
            shape.text_size = 1 / dbu
            box = Box(0, 0, len(error) * shape.text_size, shape.text_size)
            shapes(LayerDevRecN).insert(box)
            return

        if "txt" in self.filetype:
            # Format: (x1,y1;x2,y2;...), where x and y values are integers
            text_file = open(file_path, "r")
            lines = text_file.readlines()
        else:
            error = "File type not available: " + self.filetype
            text = Text(error, Trans(0, 0))
            shape = shapes(TextLayerN).insert(text)
            shape.text_size = 1 / dbu
            box = Box(0, 0, len(error) * shape.text_size, shape.text_size)
            shapes(LayerDevRecN).insert(box)
            return

        p = SimplePolygon().from_s(lines[0])
        shapes(LayerSiN).insert(p)

        # Create the pins on the waveguides, as short paths:
        from SiEPIC._globals import PIN_LENGTH as pin_length

        bbox = p.bbox()
        y = (bbox.p1.y + bbox.p2.y) / 2
        leftx = bbox.left
        port_w = to_itype(self.port_w, dbu)
        pin = Path([Point(pin_length / 2, 0), Point(-pin_length / 2, 0)], port_w)

        t = Trans(Trans.R0, bbox.left, y)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin1", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        t = Trans(Trans.R180, bbox.right, y)
        pin_t = pin.transformed(t)
        shapes(LayerPinRecN).insert(pin_t)
        text = Text("pin2", t)
        shape = shapes(LayerPinRecN).insert(text)
        shape.text_size = 0.4 / dbu

        # Create the device recognition layer -- make it 1 * wg_width away from the waveguides.
        box = Box(bbox.left, y - 3 / 2 * port_w, bbox.right, y + 3 / 2 * port_w)
        shapes(LayerDevRecN).insert(box)
