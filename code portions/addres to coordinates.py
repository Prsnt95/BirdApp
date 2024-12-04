# -*- coding: utf-8 -*-
"""
@author: dmonz
"""

import osmnx as ox

address = "2145 Sheridan Rd, Evanston, IL 60208"

origin_coordinates = ox.geocode(address)
print(origin_coordinates)
