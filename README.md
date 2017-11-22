# accra_transit_gif

This repository is a tool that downloads an OSM history file and generates a GIF animation of the evolution of the transit data mapping.

It is a fork of [Jungle-Bus/accra_transit_gif](https://github.com/Jungle-Bus/accra_transit_gif) and adapted to the urban transport of Estelí, Nicaragua.

![result in Estelí](result.gif)

## Requirements

To use this tool, you need :
* python3
* phantomjs (https://gist.github.com/julionc/7476620)
* some python dependencies (see `requirements.txt`)
* for osmium, you need to install 'libboost-python-dev' and the [libosmosium dependencies](http://osmcode.org/libosmium/manual.html#dependencies)

## How to run
To run this tool, execute this command line `python3 transit_to_gif.py`.
