# coding: utf-8

# Export des données Transport du Ghana

import os
import requests
import shutil
import datetime
import osmium
import pandas as pd
from shapely.geometry import LineString, MultiLineString
from shapely.ops import cascaded_union
import transit_to_gif_handlers

### ESTELI
'''CONFIG_START_DATE = datetime.datetime.strptime('2016-10-01', '%Y-%m-%d')
CONFIG_DELTA_DAYS = 10
CONFIG_END_DATE   = datetime.datetime.strptime('2017-11-22', '%Y-%m-%d')
CONFIG_BOUNDING   = {"top": 13.1183, "bottom": 13.0608, "left": -86.3806, "right": -86.3324} #TODO change right to top and other way round!!
CONFIG_OSH_URL    = 'http://download.geofabrik.de/central-america/nicaragua.osh.pbf'
CONFIG_OSH_FILE   = './nicaragua.osh.pbf'
CONFIG_RESULT_GIF = './result-esteli.gif'
CONFIG_LOCATION   = 'Estelí, Nicaragua'
CONFIG_ZOOM       = 14'''

### MANAGUA
CONFIG_START_DATE = datetime.datetime.strptime('2012-01-01', '%Y-%m-%d')
CONFIG_DELTA_DAYS = 60
CONFIG_END_DATE   = datetime.datetime.strptime('2017-11-22', '%Y-%m-%d')
CONFIG_BOUNDING   = {"top": 12.2048, "bottom": 12.0608, "left": -86.3865, "right": -86.1452}
CONFIG_OSH_URL    = 'http://download.geofabrik.de/central-america/nicaragua.osh.pbf'
CONFIG_OSH_FILE   = './nicaragua.osh.pbf'
CONFIG_RESULT_GIF = './result-managua.gif'
CONFIG_LOCATION   = 'Managua, Nicaragua'
CONFIG_ZOOM       = 12



if not os.path.isfile(CONFIG_OSH_FILE):
    print("Downloading {}".format(CONFIG_OSH_FILE))
    with open(CONFIG_OSH_FILE, "wb") as file:
        r = requests.get(CONFIG_OSH_URL) # TODO: loading in memory
        file.write(r.content)
    print("Downloaded !")
else:
    print("File {} already exists".format(CONFIG_OSH_FILE))


#===============================================
#              Load Stops
stops_file = './stops.csv'
stops = []
if not os.path.isfile(stops_file):
    print("Le fichier {} n'existe pas, lancement du traitement".format(stops_file))
    stops_handler = transit_to_gif_handlers.StopsHandler(CONFIG_START_DATE)
    stops_handler.apply_file(CONFIG_OSH_FILE)

    #on charge dans stops les données finales, avec la 1ère date de modification après le 1er juillet 2017
    #et le dernier nom et la dernière position connus
    for k,v in stops_handler.stops.items():
        min_version = min(v["version"])
        min_index = v["version"].index(min_version)
        max_version = max(v["version"])
        max_index = v["version"].index(max_version)
        s = {
             "object_id": k,
             "creation_date": v["date"][min_index],
             "last_modif_date": v["date"][max_index],
             "last_name": v["name"][max_index],
             "last_lat": v["lat"][max_index],
             "last_lon": v["lon"][max_index],
             "last_geometry": v["geometry"][max_index]
            }
        stops.append(s)

    pd.DataFrame.from_dict(stops).to_csv('./stops.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(stops_file))
stops = pd.read_csv(stops_file, parse_dates=["creation_date"]).to_dict(orient="records")
print('fin de chargement des stops : {:d}'.format(len(stops)))

#===============================================
#              Load Relations
routes_file1 = "./routes.csv"
routes = []
routes_all_ways = []
if not os.path.isfile(routes_file1):
    print("Le fichier {} n'existe pas, lancement de la lecture des relations".format(routes_file1))
    routes_handler = transit_to_gif_handlers.RelationHandler(CONFIG_START_DATE)
    routes_handler.apply_file(CONFIG_OSH_FILE)

    for k,v in routes_handler.routes.items():
        min_version = min(v["version"])
        min_index = v["version"].index(min_version)
        max_version = max(v["version"])
        max_index = v["version"].index(max_version)
        r = {
             "object_id": k,
             "creation_date": v["date"][min_index],
             "last_modif_date": v["date"][max_index],
             "last_ref": v["ref"][max_index],
             "last_name": v["name"][max_index],
             "last_ways": v["ways"][max_index]
            }
        routes_all_ways.extend(r["last_ways"])
        routes.append(r)

    #il faut ensuite charger les dernières versions des ways utilisés par les relations pour avoir la géometrie
    pd_routes = pd.DataFrame.from_dict(routes)
    pd_routes.to_csv('./routes.csv')
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(routes_file1))
routes = pd.read_csv(routes_file1, parse_dates=["creation_date"]).to_dict(orient="records")
for r in routes:
    #liste stockée comme chaine de caractères => on la parse à la main (plus simple)
    ways = r["last_ways"][1:-1]
    ways = ways.split(",")
    ways = [int(i) for i in ways if i]
    r["last_ways"] = ways
    routes_all_ways.extend(ways)
print('fin de chargement des relations : {:d} (dont {:d} références de ways)'.format(len(routes), len(routes_all_ways)))


#===============================================
#              Load Ways
ways_file = "./ways.csv"
ways_all_nodes = []
routes_all_ways = set(routes_all_ways) #utilisation d'un set pour sacrément accélerer la vérif de présence d'un item /!\
if not os.path.isfile(ways_file):
    print("Le fichier {} n'existe pas, lancement de la lecture des ways".format(ways_file))
    way_handler = transit_to_gif_handlers.WayHandler(routes_all_ways)
    way_handler.apply_file(CONFIG_OSH_FILE)
    print("Ecriture du fichier {}".format(ways_file))
    ways = [w for w in way_handler.ways.values()]
    pd.DataFrame.from_dict(ways).to_csv(ways_file)
else:
    print("Le fichier {} existe, chargement depuis le fichier".format(ways_file))
ways = pd.read_csv(ways_file).to_dict(orient="records")
for w in ways:
    points = w["nodes_ref"][1:-1]
    points = points.split(",")
    points = [int(i) for i in points if i]
    ways_all_nodes.extend(points)
    w["nodes_ref"] = points
print("Chargement des ways terminé : {:d}".format(len(ways)))
print("nombre de refs de node : {:d}".format(len(ways_all_nodes)))


#===============================================
#              Load Nodes
#pas de sauvegarde fichier pour les nodes, le chargement est rapide
ways_all_nodes = set(ways_all_nodes)
routes_handler3 = transit_to_gif_handlers.NodeHandler(ways_all_nodes)
routes_handler3.apply_file(CONFIG_OSH_FILE)
nodes = routes_handler3.nodes
print("Chargement des nodes terminé : {:d}".format(len(nodes)))


#===============================================
print("Construction des géometries des ways")
for w in ways:
    w_nodes = []
    for wn in w["nodes_ref"]:
        n = nodes[wn]
        w_nodes.append((n["lat"], n["lon"]))
    w["geom_raw"] = w_nodes
    w["geom"] = LineString(w_nodes)

#===============================================
print("Construction des géometries des relations")
for r in routes:
    r_ways = []
    r_ways_geom = []
    for rw in r["last_ways"]:
        for w in ways:
            if w["object_id"] == rw:
                r_ways.append(w["geom_raw"])
                r_ways_geom.append(w["geom"])
                break
    r["geom_raw"] = r_ways
    try:
        r["geom"] = MultiLineString(r_ways_geom)
    except:
        print(r_ways_geom)


#===============================================
print("Chargement de la carte")
import folium
from folium.plugins import MarkerCluster
from PIL import Image
from PIL import ImageFont
from PIL import ImageDraw

def show_date_on_image(image_path, date_to_display, nb_stops, nb_routes):
    print("modification de l'image")
    img = Image.open(image_path)
    draw = ImageDraw.Draw(img)
    # Affichage du titre # TODO: compute this one!
    text_offset = [410, 40]
    text_border = 5
    text_length = 640
    text_size = 24
    font = ImageFont.truetype('Pillow/Tests/fonts/LiberationMono-Bold.ttf', text_size)
    draw.rectangle([
        text_offset[0] - text_border,
        text_offset[1] - text_border,
        text_offset[0] + text_border + text_length,
        text_offset[1] + text_border + text_size
        ], fill='#858687')
    text_to_display = "OpenStreetMap bus routes in "+CONFIG_LOCATION
    draw.text((text_offset[0], text_offset[1]), text_to_display,'#000000',font=font)
    # Affichage de la date
    text_offset = [img.size[0] - 400, img.size[1] - 50]
    text_border = 4
    text_length = 119
    text_size = 20
    font = ImageFont.truetype('Pillow/Tests/fonts/LiberationMono-Bold.ttf', text_size)
    draw.rectangle([
        text_offset[0] - text_border,
        text_offset[1] - text_border,
        text_offset[0] + text_border + text_length,
        text_offset[1] + text_border + text_size
        ], fill='#858687')
    draw.text((text_offset[0], text_offset[1]), date_to_display.strftime('%Y-%m-%d'),'#000000',font=font)
    # Affichage du nombre d'arrêts
    text_offset = [img.size[0] - 400, img.size[1] - 120]
    text_border = 2
    text_length = 230
    text_size = 14
    font = ImageFont.truetype('Pillow/Tests/fonts/LiberationMono-Bold.ttf', text_size)
    draw.rectangle([
        text_offset[0] - text_border,
        text_offset[1] - text_border,
        text_offset[0] + text_border + text_length,
        text_offset[1] + text_border + text_size
        ], fill='#858687')
    text_to_display = "{: >4} bus routes".format(nb_routes)
    draw.text((text_offset[0], text_offset[1]), text_to_display,'#000000',font=font)
    # Affichage du nombre de routes
    text_offset = [img.size[0] - 400, img.size[1] - 90]
    text_border = 2
    text_length = 230
    text_size = 14
    font = ImageFont.truetype('Pillow/Tests/fonts/LiberationMono-Bold.ttf', text_size)
    draw.rectangle([
        text_offset[0] - text_border,
        text_offset[1] - text_border,
        text_offset[0] + text_border + text_length,
        text_offset[1] + text_border + text_size
        ], fill='#858687')
    text_to_display = "{: >4} bus stops and platforms".format(nb_stops)
    draw.text((text_offset[0], text_offset[1]), text_to_display,'#000000',font=font)
    # Enregistrement de l'image
    img_croped = img.crop((50, 0, img.size[0], img.size[1]))
    img.close()
    img_croped.save(image_path)

attributions = "cartodb | © OpenStreetMap"
tiles = 'https://cartodb-basemaps-{s}.global.ssl.fastly.net/dark_all/{z}/{x}/{y}.png'
location = [(CONFIG_BOUNDING["top"]+CONFIG_BOUNDING["bottom"])/2, (CONFIG_BOUNDING["left"]+CONFIG_BOUNDING["right"])/2]
m = folium.Map(location=location, zoom_start=CONFIG_ZOOM, # TODO: compute zoom level by bounding box
    max_zoom=CONFIG_ZOOM, min_zoom=CONFIG_ZOOM,
    attr=attributions, tiles=tiles, png_enabled=True)

img_tmp_dir = './tmp_images'
if os.path.exists(img_tmp_dir):
    shutil.rmtree(img_tmp_dir)
os.makedirs(img_tmp_dir)

date_cursor = CONFIG_START_DATE
for r in routes:
    r["displayed"] = False
for s in stops:
    s["displayed"] = False
nb_routes_displayed = 0
nb_stops_displayed = 0
while date_cursor <= CONFIG_END_DATE:
    for r in routes:
        if not r["displayed"] and r["creation_date"] < pd.to_datetime(date_cursor):
            r["displayed"] = True
            
            (lat1, lon1, lat2, lon2) = (0, 0, 0, 0)
            if len(r["geom_raw"]) > 0 and len(r["geom_raw"][0]) > 0:
                (lat1, lon1) = r["geom_raw"][0][0]
                test = r["geom_raw"][len(r["geom_raw"])-1]
                if len(test) > 0:
                    (lat2, lon2) = test[len(test)-1]
            
            if float(lat1) <= CONFIG_BOUNDING["top"] and float(lat1) >= CONFIG_BOUNDING["bottom"] \
            and float(lon1) >= CONFIG_BOUNDING["left"] and float(lon1) <= CONFIG_BOUNDING["right"] \
            and float(lat2) <= CONFIG_BOUNDING["top"] and float(lat2) >= CONFIG_BOUNDING["bottom"] \
            and float(lon2) >= CONFIG_BOUNDING["left"] and float(lon2) <= CONFIG_BOUNDING["right"]:
                folium.PolyLine(r["geom_raw"], color="#1779c2", weight=1.5, opacity=1).add_to(m)
                nb_routes_displayed += 1
    for s in stops:
        if not s["displayed"] and s["creation_date"] < pd.to_datetime(date_cursor):
            s["displayed"] = True
            if float(s["last_lat"]) <= CONFIG_BOUNDING["top"] and float(s["last_lat"]) >= CONFIG_BOUNDING["bottom"] \
            and float(s["last_lon"]) >= CONFIG_BOUNDING["left"] and float(s["last_lon"]) <= CONFIG_BOUNDING["right"]:
                folium.Circle([s["last_lat"], s["last_lon"]], radius=2.5, color="#1779c2", opacity=1).add_to(m)
                nb_stops_displayed += 1
    print("Enregistrement de la carte pour la date du {}".format(date_cursor.strftime('%Y-%m-%d')))
    image_path = os.path.join(img_tmp_dir, "image_{}.png".format(date_cursor.strftime('%Y-%m-%d')))
    with open(image_path, "wb")  as image_file:
        m._png_image = None #on réinitialise le PNG
        image_file.write(m._to_png())
    show_date_on_image(image_path, date_cursor, nb_stops_displayed, nb_routes_displayed)
    date_cursor = date_cursor + datetime.timedelta(days=CONFIG_DELTA_DAYS)

#===============================================
print("Création du GIF")
import imageio

file_names = sorted((os.path.join(img_tmp_dir, fn) for fn in os.listdir(img_tmp_dir) if fn.endswith('.png')))

with imageio.get_writer(CONFIG_RESULT_GIF, mode='I', duration=0.4) as writer: # TODO: change name!
    for filename in file_names:
        image = imageio.imread(filename)
        writer.append_data(image)
