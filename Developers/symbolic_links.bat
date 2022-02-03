:: for Windows
:: GitHub repository installation of SiEPIC files for KLayout

:: assumes that 
:: - SiEPIC-* repositories are in the user's profile directory, under Documents/GitHub
:: - KLAYOUT_HOME is in the user's profile directory, as KLayout

mklink /d %userprofile%\KLayout\tech\EBeam %userprofile%\Documents\GitHub\SiEPIC_EBeam_PDK\klayout_dot_config\tech\EBeam

mkdir %userprofile%\KLayout\Lumerical_CMLs
mklink /d %userprofile%\KLayout\Lumerical_CMLs\EBeam %userprofile%\Documents\GitHub\SiEPIC_EBeam_PDK\Lumerical_EBeam_CML\EBeam

