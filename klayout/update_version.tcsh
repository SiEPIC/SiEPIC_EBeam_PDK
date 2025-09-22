#!/bin/tcsh 
 

# update version number:
find . \( -name '__init__.py' -o -name 'EBeam.lyt' -o -name 'grain.xml' -o -name 'pyproject.toml' \) -type f \
    -exec sh -c 'sed -i "" -e "s/0.4.47/0.4.49/g" "$1" && echo "file: $1"' sh {} \;



