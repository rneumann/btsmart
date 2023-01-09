How to build the library
========================

Here are the steps to build the library

.. code-block:: sh

    ver=[enter version here]
    python3 -m pip install build
    python3 -m build --sdist
    python3 -m build --wheel
    twine check dist/*

Locally install the created package

.. code-block:: sh
    pip3 uninstall -y btsmart
    pip3 install dist/btsmart-$(ver)*.whl

Uploading the package to pypi

.. code-block:: sh
    twine upload dist/btsmart-$(ver)*

And this is how to install the result

.. code-block:: sh

    pip uninstall btsmart
    pip install btsmart==$ver




