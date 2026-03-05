import json
import pyproj
import unexecore.geofile
import os

def round_floats(o):
    if isinstance(o, float):
        return round(o, 6)
    if isinstance(o, dict):
        return {k: round_floats(v) for k, v in o.items()}
    if isinstance(o, (list, tuple)):
        return [round_floats(x) for x in o]
    return o


def asc_to_geojson(asc_file:unexecore.geofile.GeoFile, src_crs: str, dest_crs: str, name:str, attribute_label:str, colour_lookup: dict = None) -> dict:
    try:
        geojson = {
            "type": "FeatureCollection",
            "name": name,
            "crs": {
                "type": "name",
                "properties": {
                    "name": dest_crs
                }
            },
            "features": []
        }

        if colour_lookup == None:
            colour_lookup = {}
            colour_lookup[0.1] = (255, 255, 255, 0)
            colour_lookup[0.5] = (206, 236, 254, 255)
            colour_lookup[1.0] = (156, 203, 254, 255)
            colour_lookup[2.0] = (114, 153, 254, 255)
            colour_lookup[4.0] = (69, 102, 254, 255)
            colour_lookup[9999999.0] = (23, 57, 206, 255)

        keys = list(colour_lookup.keys())
        keys.sort()
        band1 = asc_file.raster_file.read(1)

        transformer = pyproj.Transformer.from_crs(src_crs, dest_crs)

        for y in range(0, asc_file.raster_file.height):
            for x in range(0, asc_file.raster_file.width):
                try:
                    v0 = band1[y, x]

                    if v0 != asc_file.raster_file.nodata and v0 > keys[0]:
                        feature = {
                            "properties": {
                                attribute_label: 0.0,
                                "color": "#000000"
                            },
                            "geometry": {
                                "type": "Polygon",
                                "coordinates": []
                            },
                            "type": "Feature"
                        }
                        # make an edge loop [0,1,2,3,0]
                        coords = [
                            [asc_file.raster_file.bounds.left + (x * asc_file.raster_file.res[0]), asc_file.raster_file.bounds.top - (y * asc_file.raster_file.res[1])],
                            [asc_file.raster_file.bounds.left + ((x + 1) * asc_file.raster_file.res[0]), asc_file.raster_file.bounds.top - (y * asc_file.raster_file.res[1])],
                            [asc_file.raster_file.bounds.left + ((x + 1) * asc_file.raster_file.res[0]), asc_file.raster_file.bounds.top - ((y + 1) * asc_file.raster_file.res[1])],
                            [asc_file.raster_file.bounds.left + (x * asc_file.raster_file.res[0]), asc_file.raster_file.bounds.top - ((y + 1) * asc_file.raster_file.res[1])],
                        ]

                        for c in range(0, len(coords)):
                            lat, lng = transformer.transform(coords[c][1], coords[c][0])
                            coords[c] = (lng, lat)

                        feature['geometry']['coordinates'].append(coords[0])
                        feature['geometry']['coordinates'].append(coords[1])
                        feature['geometry']['coordinates'].append(coords[2])
                        feature['geometry']['coordinates'].append(coords[3])
                        feature['geometry']['coordinates'].append(coords[0])

                        feature['geometry']['coordinates'] = [feature['geometry']['coordinates']]
                        feature['properties'][attribute_label] = float(v0)

                        for i in range(0, len(keys) - 1):
                            if v0 >= keys[i] and v0 < keys[i + 1]:
                                feature['properties']['color'] = unexecore.geofile.rgba2hex(colour_lookup[keys[i + 1]])

                        geojson['features'].append(feature)
                except Exception as e:
                    print(unexecore.debug.exception_to_string(e))
        return round_floats(geojson)
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    return {}


def asc_get_info(asc_file:unexecore.geofile.GeoFile) -> dict:

    info = {}
    try:
        band1 = asc_file.raster_file.read(1)

        for y in range(0, asc_file.raster_file.height):
            for x in range(0, asc_file.raster_file.width):
                try:
                    v0 = band1[y, x]

                    if v0 != asc_file.raster_file.nodata:
                        if v0 not in info:
                            info[v0] = 0
                        info[v0]+=1

                except Exception as e:
                    print(unexecore.debug.exception_to_string(e))
    except Exception as e:
        print(unexecore.debug.exception_to_string(e))

    return info


def dump_visualisations(result:dict, output_filepath:str):
    work_list = {'current': ['peak'], 'nowcast': ['peak'], 'forecast': ['peak', '1day', '2day', 'end']}

    result_path = output_filepath + os.sep

    if not os.path.exists(result_path):
        os.makedirs(result_path)
    else:
        unexecore.file.deltree(result_path)


    colour_lookup = {}
    colour_lookup[0.1] = (255, 255, 255, 0)
    colour_lookup[0.5] = (206, 236, 254, 255)
    colour_lookup[1.0] = (156, 203, 254, 255)
    colour_lookup[2.0] = (114, 153, 254, 255)
    colour_lookup[4.0] = (69, 102, 254, 255)
    colour_lookup[9999999.0] = (23, 57, 206, 255)


    work_list = {'current': ['peak'], 'nowcast': ['peak'], 'forecast': ['peak', '1day', '2day', 'end']}

    for key, value in work_list.items():
        for item in value:
            asc_file = unexecore.geofile.GeoFile()
            asc_file.loadASC(result[key][item])

            name = key + '_' + item

            im = asc_file.get_png(colour_lookup)
            im.save(result_path + name + '.png')

            geojson = asc_to_geojson(asc_file, 'EPSG:3035', 'EPSG:4326', colour_lookup)
            with open(result_path + name + '.geojson', 'w') as f:
                json.dump(geojson, f)

    # result['caflood_src']['dem'] -> greyscale
    # result['caflood_src']['land'] -> lookup
    # result['caflood_src']['rain'] -> lookup
