How to build the library
========================

Here are the steps to build the library

.. code-block:: sh

    ver=[enter version here]
    python3 -m pip install build
    python3 -m build --sdist
    python3 -m build --wheel
    twine check dist/*
    twine upload dist/btsmart-$(ver)*

And This is how to locally test the result

.. code-block:: sh

    pip uninstall btsmart
    pip install btsmart==$ver
