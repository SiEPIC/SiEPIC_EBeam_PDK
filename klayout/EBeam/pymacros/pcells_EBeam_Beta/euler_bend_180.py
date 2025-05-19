import pya
from pya import *
from pya import Text

from SiEPIC._globals import Python_Env
if Python_Env == 'Script':
    # For external Python mode, when installed using pip install siepic_ebeam_pdk
    import siepic_ebeam_pdk

from SiEPIC.utils.layout import new_layout, make_pin
from SiEPIC.utils import translate_from_normal, get_technology_by_name

class euler_bend_180(pya.PCellDeclarationHelper):
    def __init__(self):
        self.cellname = self.__class__.__name__
        super(eval(self.cellname), self).__init__()
        
        self.technology_name = "EBeam"
        self.TECHNOLOGY = get_technology_by_name(self.technology_name)
        
        self.param("radius",self.TypeDouble,"Effective Radius",default=5)
        self.param("p",self.TypeDouble,"Euler Parameter",default=0.25)
        self.param("ww",self.TypeDouble,"Waveguide Width",default=0.5)
        self.param("layer", self.TypeLayer, "Layer", default=self.TECHNOLOGY["Si"])
        self.param("shape_only", self.TypeBoolean, "Only draw the shapes for fabrication", default=False, hidden=True)
    
    def display_text_impl(self):
        # Provide a descriptive text for the cell
        return "euler_bend_180_%.1f-%.1f-%.1f" % (
            self.radius,
            self.p,
            self.ww,
        )
    
    def produce_impl(self):
        dbu = self.layout.dbu
        ly = self.layout
        shapes = self.cell.shapes
        TECHNOLOGY = self.TECHNOLOGY
        
        radius = (self.radius)/dbu
        p = self.p
        ww = (self.ww)/dbu
        
        DevRec_lay = TECHNOLOGY["DevRec"]
        Si_lay = self.layer
        PinRec_lay = TECHNOLOGY["PinRec"]        
        
        path, Rmin, fraction_circular = self.euler_points(radius,p)
        wg_pts = pya.Path(path, 0).unique_points().get_points()
        wg_polygon = pya.Polygon(translate_from_normal(wg_pts, ww/2) + translate_from_normal(wg_pts, -ww/2)[::-1])
        waveguide_length = wg_polygon.area()/ww
        shapes(Si_lay).insert(wg_polygon)
        
        if not self.shape_only:
            # Device Recognition layer:
            path, Rmin, fraction_circular = self.euler_points(radius,p, DevRec=True)
            wg_pts = pya.Path(path, 0).unique_points().get_points()
            wg_polygon = pya.Polygon(translate_from_normal(wg_pts, 1.5*ww) + translate_from_normal(wg_pts, -1.5*ww)[::-1])
            shapes(DevRec_lay).insert(wg_polygon)

            # Pins        
            make_pin(self.cell,"opt1",[0,0],ww/1000,ly.layer(PinRec_lay),180)
            make_pin(self.cell,"opt2",[0,radius*2],ww/1000,ly.layer(PinRec_lay),180)

            # Compact model information
            t = pya.Trans(pya.Trans.R0, 0, 0)
            text = Text("Lumerical_INTERCONNECT_library=EBeam", t, ww/10, -1)
            shape = shapes(DevRec_lay).insert(text)
            shape.text_size = ww / 10
            t = pya.Trans(pya.Trans.R0, 0, ww / 4)
            text = pya.Text("Component=ebeam_wg_integral_1550", t, ww/10, -1)
            shape = shapes(DevRec_lay).insert(text)
            shape.text_size = ww / 10
            t = pya.Trans(pya.Trans.R0, 0, ww / 2)
            text = Text(
                "Spice_param:wg_length=%.3fu wg_width=%.3fu"
                % (waveguide_length * dbu, ww*dbu), t, ww / 10, -1
            )
            shape = shapes(DevRec_lay).insert(text)
            
        t = pya.Trans(pya.Trans.R0, 0, -ww)
        text = Text(
            'Length=%.3f (microns)' % (waveguide_length*dbu), t, ww / 3, -1)
        shape = shapes(DevRec_lay).insert(text)
        t = pya.Trans(pya.Trans.R0, 0, ww)
        text = Text(
            'Minimum bend radius=%.2f (microns)' % (Rmin), t, ww * .2, -1)
        shape = shapes(DevRec_lay).insert(text)
        t = pya.Trans(pya.Trans.R0, 0, ww*0.75)
        text = Text(
            f'Circular bend fraction={fraction_circular*100:.1f}%', t, ww * .1, -1)
        shape = shapes(DevRec_lay).insert(text)
        
    def can_create_from_shape(self, layout, shape, layer):
        return False
    
    @staticmethod
    def euler_points(radius=5e3, p_in=0.25, DevRec=None, dbu=0.001, debug=False):
        '''Function to create points for a 180 degree Euler bend with 
        radius and a user-specified bend parameter 'p'.
        Inspired from GDS factory code [1] and the 2019 Vogelbacher et al. paper:
        'Analysis of silicon nitride partial Euler waveguide bends' [2].
        
        Developed by Evan Jonker, May 2025
        
        [1] https://github.com/gdsfactory/gdsfactory/blob/main/gdsfactory/path.py
        [2] https://dx.doi.org/10.1364/oe.27.031394
        
            INPUTS:
                radius (float): desired effective radius 
                p (float): bend parameter, must be between 0.0 and 1.0
        '''
        from SiEPIC.utils import points_per_circle
        import numpy as np
        import scipy.integrate as integrate
        import pya

        # number of points for a quarter circle
        N = points_per_circle(radius/1000, dbu=dbu)/4
        if DevRec:
            npoints = int(N / 3)
        else:
            npoints = int(N)
        if npoints < 5:
            npoints = 100

        # Internal variables
        angle = 180
        if debug:
            print("npoints = {}".format(npoints))
        R0 = 1
        alpha = np.radians(angle)
        Rp = R0 / np.sqrt(p_in * alpha)
        sp = R0 * np.sqrt(p_in * alpha)
        s0 = 2 * sp + Rp * alpha * (1 - p_in)

        # Allocate points for euler-bend and circular sections
        num_pts_euler = int(np.round(sp / (s0 / 2) * npoints))
        num_pts_arc = npoints - num_pts_euler
        # For low number of points (DevRec) there may not be any circular section
        # Make sure there are at least 2 points allocated for the circle
        if debug:
            print(f'num_pts_arc: {num_pts_arc}, euler {num_pts_euler}, total {npoints}')
        if num_pts_arc < 2:
            num_pts_euler = npoints-2
            num_pts_arc = 2
            if debug:
                print(f'num_pts_arc: {num_pts_arc}, euler {num_pts_euler}, total {npoints}')
        fraction_circular = num_pts_arc / npoints

        # Calculate [x,y] of euler-bend by numerically solving fresnel integrals
        s_euler = np.linspace(0, sp, num_pts_euler)
        xbend1 = np.zeros(num_pts_euler)
        ybend1 = np.zeros(num_pts_euler)
        for i, s_pt in enumerate(s_euler):
            xbend1[i], _ = integrate.quad(lambda t: np.cos((t/R0)**2 / 2), 0, s_pt)
            ybend1[i], _ = integrate.quad(lambda t: np.sin((t/R0)**2 / 2), 0, s_pt)

        # Determine the offset for the circular section
        xp, yp = xbend1[-1], ybend1[-1]
        dx = xp - Rp * np.sin(p_in * alpha / 2)
        dy = yp - Rp * (1 - np.cos(p_in * alpha / 2))

        # Calculate [x,y] for the circular-bend section
        s_arc = np.linspace(sp, s0 / 2, num_pts_arc)
        xbend2 = Rp * np.sin((s_arc - sp) / Rp + p_in * alpha / 2) + dx
        ybend2 = Rp * (1 - np.cos((s_arc - sp) / Rp + p_in * alpha / 2)) + dy

        # Join euler-bend and circular sections
        x = np.concatenate([xbend1, xbend2[1:]])
        y = np.concatenate([ybend1, ybend2[1:]])

        # Evaluate effective radius before re-scaling
        Reff = 2*y[-1]

        # Determine second half of the bend as the a mirror of the first
        points2 = np.array([np.flipud(x), np.flipud(Reff - y)]).T

        # Scale the curve to match the desired radius
        scale = 2*radius / Reff
        points = np.concatenate([np.array([x, y]).T[:-1], points2]) * scale
        
        # The minimum radius is Rp
        Rmin = round(Rp * scale/1000,3)
        if debug:
            print(f"   [euler_bend_180] minimum bend radius: {Rmin} microns")

        # Code to plot bend curvatures
        if False:
            dx = np.gradient(points[:,0])
            dy = np.gradient(points[:,1])
            ddx = np.gradient(dx)
            ddy = np.gradient(dy)
            curvature = (dx * ddy - dy * ddx) / (dx**2 + dy**2)**1.5
            ptnums = np.arange(len(points[:,0]))
            arr = points[:,0]
            
            half = arr[:len(arr)//2]
            second_half = arr[len(arr)//2:]
            
            half_c = curvature[:len(curvature)//2]
            second_half_c = curvature[len(curvature)//2:]

            import matplotlib.pyplot as plt
            plt.figure(1)
            plt.plot(ptnums,curvature)
            plt.xlabel("pt number")
            plt.ylabel("curvature")
            
            plt.figure(2)
            plt.plot(half,half_c,linestyle='--')
            plt.plot(second_half,second_half_c,linestyle='--')
            plt.xlabel("pt x-coord")
            plt.ylabel("curvature")
            plt.legend(["bottom half","top half"])
            plt.show()
        
        # Create array of "Point" types
        pts = []
        for i in range(len(points)):
            pts.append(pya.Point(round(points[i,0]), round(points[i,1])))

        if debug:
            print("Euler pts (float): {}".format(points))
            print("Euler pts (Point): {}".format(pts))
        
        return pts, Rmin, fraction_circular

        
class test_lib(Library):
    def __init__(self):
        tech = "EBeam"
        library = tech + "test_lib"
        self.technology = tech
        self.layout().register_pcell("euler_bend_180", euler_bend_180())
        self.register(library)

if __name__ == "__main__":
    print("Test layout for: euler_bend_180")

    # load the test library, and technology
    t = test_lib()
    tech = t.technology

    # Create a new layout for the chip floor plan
    topcell, ly = new_layout(tech, "test", GUI=True, overwrite=True)

    # instantiate the cell
    library = tech + "test_lib"

    # Create spirals for all the types of waveguides
    from SiEPIC.utils import load_Waveguides_by_Tech

    waveguide_types = load_Waveguides_by_Tech(tech)
    technology = get_technology_by_name('EBeam')
    xmax = 0
    y = 0
    x = xmax
    pcell = ly.create_cell(
        "euler_bend_180",
        library,{
                "p": 0.3,
                "ww": 0.5,
                "radius": 5,
        })
    t = pya.Trans(pya.Trans.R0, x, y - pcell.bbox().bottom)
    inst = topcell.insert(pya.CellInstArray(pcell.cell_index(), t))

    # Display in KLayout, saving the layout in the PCell's folder
    import os
    topcell.show(os.path.dirname(__file__))
