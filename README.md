# Sensirion Drvier Adapters

This repository contains adapter classes that can be used to separate the
logic of packaging user data into a byte stream and using that byte
stream in different channels.
The classes can be used as adapters to the *sensirion_i2c_driver.I2cConnection* and
*sensirion_shdlc_driver.ShdlcSerialPort*.

The python package sensirion-driver-adapters replaces the package sensirion-i2c-adapter. The latter is deprecated and
will no longer be maintained. All functionality of sensirion-i2c-adapter is contained within the package
sensirion-driver-adapters.

## Usage

See package description in [README.rst](README.rst) and user manual at
https://sensirion.github.io/python-driver-adapters/.

## Development

We develop and test this driver using our company internal tools (version
control, continuous integration, code review etc.) and automatically
synchronize the `master` branch with GitHub. But this doesn't mean that we
don't respond to issues or don't accept pull requests on GitHub. In fact,
you're very welcome to open issues or create pull requests :)

### Check coding style

The coding style can be checked with [`flake8`](http://flake8.pycqa.org/):

```bash
pip install -e .[test]  # Install requirements
flake8                  # Run style check
```

### Run tests

Unit tests can be run with [`pytest`](https://pytest.org/):

```bash
pip install -e .[test]          # Install requirements
pytest                          # Run tests
```

### Build documentation

The documentation can be built with [Sphinx](http://www.sphinx-doc.org/):

```bash
python setup.py install                        # Install package
pip install -r docs/requirements.txt           # Install requirements
sphinx-versioning build docs docs/_build/html  # Build documentation
```


## License

See [LICENSE](LICENSE).
