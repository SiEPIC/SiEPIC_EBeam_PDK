#!/bin/bash

# OSX GitHub repository installation of SiEPIC files for KLayout and Lumerical INTERCONNECT

# assumes that 
# - SiEPIC-* repositories are in ~/Documents/GitHub
# - KLAYOUT_HOME is ~/.klayout

# to run:
# source symbolic_links_from_GitHub_to_KLayout.sh

export SRC=$HOME/Documents/GitHub
export DEST=$HOME/.klayout
export INTC=$HOME/.config/Lumerical
export REPO=SiEPIC_EBeam_PDK

mkdir $DEST/tech
ln -s $SRC/$REPO/klayout_dot_config/tech/* $DEST/tech/
ln -s $SRC/$REPO/klayout_dot_config/pymacros/* $DEST/pymacros

ln -s $SRC/$REPO/Lumerical_EBeam_CML/EBeam $INTC/Custom/
ln -s $SRC/$REPO/Lumerical_EBeam_CML/EBeam-dev $INTC/Custom/

grep -q -F '[Design%20kits]' $INTC/INTERCONNECT.ini || echo '[Design%20kits]' >> $INTC/INTERCONNECT.ini

grep -q -F '/EBeam' $INTC/INTERCONNECT.ini || sed -i .bak '/Design/a\
EBeam='$SRC/$REPO'/Lumerical_EBeam_CML/EBeam
' $INTC/INTERCONNECT.ini

grep -q -F '/EBeam-dev' $INTC/INTERCONNECT.ini || sed -i .bak '/Design/a\
EBeam-dev='$SRC/$REPO'/Lumerical_EBeam_CML/EBeam-dev
' $INTC/INTERCONNECT.ini

