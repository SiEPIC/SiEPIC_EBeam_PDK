This folder contains the source files used to create the Compact Model Library

To make updates to the library:

1) make changes to the library, update the version folder with the current date (v1.2.2017_12_23)

2) package the CML:
zip -r EBeam_v2010_01_14.cml EBeam
(with the current date)

3) For KLayout integration:
		Copy the .cml file into:
		../klayout_dot_config/tech/EBeam

