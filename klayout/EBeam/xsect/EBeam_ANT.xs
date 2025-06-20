#	SiEPIC EBeam PDK cross-section, based on ANT NanoSOI process
#	https://www.appliednt.com/nanosoi/
#	Mustafa Hammood		mustafa@siepic.com

# Added SiN, by Lukas Chrostowski, 2023-02

# input layers:

si = layer("1/0")
sin = layer("4/0")
sietch1 = layer("11/0")
sietch2 = layer("12/0")

ml = layer("12/0")
mlopen = layer("13/0")
mh = layer("11/0")



# cross section calculations

# thickness of the stack
height(7.5)
depth(4)
substrate = bulk

x_oxide = grow(2.0)

# silicon layer, and etching
x_si = mask(si).grow(0.22)
etch_si = si.inverted 
# waveguide, assume 3 degree sidewall, with mid-point being the desired width; bias = sin(3)*220.
etch_angle = 3
mask(etch_si).etch(0.22, :taper => etch_angle, :bias =>  0, :into => x_si) 
x_si1 = x_si.dup

# silicon nitride layer, and etching
x_sin = mask(sin).grow(0.4)
etch_sin = sin.inverted 
# waveguide, assume 5 degree sidewall, with mid-point being the desired width; bias = sin(10)*220.
etch_angle = 5
mask(etch_sin).etch(0.4, :taper => etch_angle, :bias =>  0, :into => x_sin) 
x_sin1 = x_sin.dup

# mh metal
x_oxide = x_oxide.or(grow(2.2, 2.2, :mode => :round ))
x_mh = mask(mh).grow(0.2)

# vl and m2 metals
x_ml = mask(ml).grow(0.7,0)

x_oxide = x_oxide.or(grow(0.3, 0.3, :mode => :round ))

#x_mlopen = mask(mlopen).grow(0.3, :into => x_oxide)
mask(mlopen).etch(0.3, :taper => etch_angle, :bias =>  0, :into => x_oxide) 

# output

layers_file(File.join(File.expand_path(File.dirname(__FILE__)), "EBeam.lyp"))
output("299/0", bulk)
output("300/0", x_oxide)
output("301/0", x_si1)
output("302/0", x_sin1)
output("345/0", x_ml)
#output("346/0", x_mlopen)
output("347/0", x_mh)


