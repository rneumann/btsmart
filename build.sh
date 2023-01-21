#!/bin/sh

ver=`grep "version" setup.cfg | sed "s/.*= //g"`
echo "Building version '$ver'"

rm dist/*

#pdoc --force --html --output-dir build src/btsmart

python3 -m pip uninstall -y btsmart==$ver
python3 -m pip install build
python3 -m build --sdist
python3 -m build --wheel
twine check dist/*

python3 -m pip uninstall -y btsmart
python3 -m pip install dist/btsmart-$ver*.whl
