from defusedxml.ElementTree import parse
from defusedxml import ElementTree
from PIL import Image
from collections import namedtuple


# Check adj. tiles for all tiles on map to determine orientation. Uses bit mask to  select correct tile from spritesheet
def checkSurrounding(tiles):
    floor_map = [[None for a in range(80)] for b in range(65)]
    for tile in tiles:
        floor_map[tile.y][tile.x] = tile

    temp = []
    m = []

    if tiles[0].name == 'Fence':
        m = [5, 3, 10, 6, 5, 3, 0, 6, 9, 8, 7, 7, 2, 8, 4, 4]
        m_gate = [17, 17, 17, 17, 17, 15, 17, 17, 17, 17, 12, 17, 17, 17, 17, 17]
    else:
        m = [0, 12, 13, 9, 4, 8, 1, 5, 15, 11, 14, 10, 3, 7, 2, 6]

    for y, tile_row in enumerate(floor_map):
        for x, tile in enumerate(tile_row):
            a = 0
            if tile is not None:
                for dx, dy, b in [(0, -1, 1), (1, 0, 2), (0, 1, 4), (-1, 0, 8)]:
                    try:
                        if floor_map[y + dy][x + dx] != None:
                            if tile.name == 'Flooring' or (tile.name == 'Fence' and not tile.growth):
                                if floor_map[y + dy][x + dx].type == tile.type:
                                    a += b
                            else:
                                a += b
                    except Exception as e:
                        pass
                if tile.growth and tile.name == "Fence":
                    orientation = m_gate[a]
                    t = 1
                else:
                    orientation = m[a]
                    t = tile.type
                temp.append(tile._replace(orientation=orientation, type=t))
    return temp


# This is a test method for returning the position location and the name of objects
# located on the players farm.
# returns a dict with an array of tuples of the form: (name, x, y)

def getFarmInfo(saveFileLocation, read_data=False):
    sprite = namedtuple('Sprite', ['name', 'x', 'y', 'w', 'h', 'index', 'type', 'growth', 'flipped', 'orientation'])

    ns = "{http://www.w3.org/2001/XMLSchema-instance}"

    farm = {}

    if read_data is False:
        root = parse(saveFileLocation).getroot()
    else:
        root = ElementTree.fromstring(saveFileLocation)

    # Farm Objects

    locations = root.find('locations').findall("GameLocation")
    s = []
    for item in locations[1].find('objects').iter("item"):
        f = False
        obj = item.find('value').find('Object')
        name = obj.find('name').text
        x = int(item.find('key').find('Vector2').find('X').text)
        y = int(item.find('key').find('Vector2').find('Y').text)
        i = int(obj.find('parentSheetIndex').text)
        t = obj.find('type').text
        a = False
        if obj.find('flipped').text == 'true':
            f = True
        if 'Fence' in name or name == 'Gate':
            t = int(obj.find('whichType').text)
            a = False
            if name == 'Gate':
                a = True
            name = 'Fence'
        else:
            name = 'Object'
        s.append(sprite(name, x, y, 0, 0, i, t, a, f, obj.find('name').text))

    d = {k[0]: [a for a in s if a[0] == k[0]] for k in s}

    try:
        farm['Fences'] = checkSurrounding(d['Fence'])
    except Exception as e:
        pass

    farm['objects'] = [a for a in s if a.name != 'Fence']

    # Terrain Features

    tf = []
    crops = []
    for item in locations[1].find('terrainFeatures').iter('item'):
        s = None
        loc = None
        f = False
        name = item.find('value').find('TerrainFeature').get(ns+'type')
        if name == 'Tree':
            t = int(item.find('value').find('TerrainFeature').find('treeType').text)
            s = int(item.find('value').find('TerrainFeature').find('growthStage').text)
            if item.find('value').find('TerrainFeature').find('flipped').text == 'true': f= True
        if name == 'Flooring':
            t = int(item.find('value').find('TerrainFeature').find('whichFloor').text)
            s = int(item.find('value').find('TerrainFeature').find('whichView').text)
        if name == "HoeDirt":
            crop = item.find('value').find('TerrainFeature').find('crop')
            if crop is not None:
                crop_x = int(item.find('key').find('Vector2').find('X').text)
                crop_y = int(item.find('key').find('Vector2').find('Y').text)
                crop_phase = int(crop.find('currentPhase').text)
                crop_location = int(crop.find('rowInSpriteSheet').text)
                if crop_location in [26, 27, 28, 29, 31]:
                    r = int(crop.find('tintColor').find('R').text)
                    g = int(crop.find('tintColor').find('G').text)
                    b = int(crop.find('tintColor').find('B').text)
                    days = int(crop.find('dayOfCurrentPhase').text)
                    o = ((r, g, b), days)
                else:
                    o = None
                crop_flip = False
                if crop.find('flip').text == 'true':
                    crop_flip = True
                crop_dead = False
                if crop.find('dead').text == 'true':
                    crop_dead = True
                crops.append(sprite('HoeDirtCrop', crop_x, crop_y, 1, 1, crop_dead, crop_location, crop_phase, crop_flip, o))
        if name == "FruitTree":
            t = int(item.find('value').find('TerrainFeature').find('treeType').text)
            s = int(item.find('value').find('TerrainFeature').find('growthStage').text)
            if item.find('value').find('TerrainFeature').find('flipped').text == 'true': f= True
        if name == "Grass":
            t = int(item.find('value').find('TerrainFeature').find('grassType').text)
            s = int(item.find('value').find('TerrainFeature').find('numberOfWeeds').text)
            loc = int(item.find('value').find('TerrainFeature').find('grassSourceOffset').text)
        x = int(item.find('key').find('Vector2').find('X').text)
        y = int(item.find('key').find('Vector2').find('Y').text)
        tf.append(sprite(name, x, y, 1, 1, loc, t, s, f, None))

    d = {k[0]: [a for a in tf if a[0] == k[0]] for k in tf}
    excludes = ['Flooring', 'HoeDirt', 'Crop']
    farm['terrainFeatures'] = [a for a in tf if a.name not in excludes]
    farm['Crops'] = crops

    try:
        farm['Flooring'] = checkSurrounding(d['Flooring'])
        farm['HoeDirt'] = checkSurrounding(d['HoeDirt'])
    except Exception as e:
        pass

    # Resource Clumps
    s = []

    for item in locations[1].find('resourceClumps').iter('ResourceClump'):
        name = item.get(ns+'type')
        if name is None:
            name = 'ResourceClump'
        t = int(item.find('parentSheetIndex').text)
        x = int(item.find('tile').find('X').text)
        y = int(item.find('tile').find('Y').text)
        w = int(item.find('width').text)
        h = int(item.find('height').text)
        s.append(sprite(name, x, y, w, h, None, t, None, None, None))

    farm['resourceClumps'] = s

    s = []
    for item in locations[1].find('buildings').iter('Building'):
        name = 'Building'
        x = int(item.find('tileX').text)
        y = int(item.find('tileY').text)
        w = int(item.find('tilesWide').text)
        h = int(item.find('tilesHigh').text)
        t = item.find('buildingType').text
        s.append(sprite(name, x, y, w, h, None, t, None, None, None))

    farm['buildings'] = s

    house = sprite('House',
                   58, 14, 10, 6,
                   int(root.find('player').find('houseUpgradeLevel').text),
                   None,
                   None,
                   None,
                   None)

    hasGreenhouse = False
    for location in locations:
        if location.find('name').text == "CommunityCenter":
            cats = location.find('areasComplete').findall('boolean')
            if cats[0].text == 'true':
                hasGreenhouse = True

    # Check for letter to confirm player has unlocked greenhouse, thanks /u/BumbleBHE
    for letter in root.find('player').find('mailReceived').iter('string'):
        if letter.text == "ccPantry":
            hasGreenhouse = True

    if hasGreenhouse:
        greenHouse = sprite('Greenhouse',
                            25, 12, 0, 6, 1,
                            None, None, None, None)
    else:
        greenHouse = sprite('Greenhouse',
                            25, 12, 0, 6, 0,
                            None, None, None, None)
    farm['misc'] = [house, greenHouse]

    return farm


def colourBox(x, y, colour, pixels, scale=8):
    for i in range(scale):
        for j in range(scale):
            try:
                pixels[x*scale + i, y*scale + j] = colour
            except IndexError:
                pass
    return pixels


# Renders a PNG of the players farm where one 8x8 pixel square is equivalent to one in game tile.
# Legend:   Shades of green - Trees, Weeds, Grass
#      Shades of brown - Twigs, Logs
#      Shades of grey - Stones, Boulders, Fences
#      Dark red - Static buildings
#      Light red - Player placed objects (Scarecrows, etc)
#      Blue - Water
#      Off Tan - Tilled Soil
def generateImage(farm):
    image = Image.open("./assets/bases/minimap_base.png")
    pixels = image.load()

    pixels[1, 1] = (255, 255, 255)

    for building in farm['buildings']:
        for i in range(building[3]):
            for j in range(building[4]):
                colourBox(building[1] + i, building[2] + j, (255, 150, 150), pixels)

    if 'terrainFeatures' in farm:
        for tile in farm['terrainFeatures']:
            name = tile.name
            if name == "Tree":
                colourBox(tile.x, tile.y, (0, 175, 0), pixels)
            elif name == "Grass":
                colourBox(tile.x, tile.y, (0, 125, 0), pixels)
            elif name == "Flooring":
                colourBox(tile.x, tile.y, (50, 50, 50), pixels)
            else:
                colourBox(tile.x, tile.y, (0, 0, 0), pixels)

    if 'HoeDirt' in farm:
        for tile in farm['HoeDirt']:
            colourBox(tile.x, tile.y, (196, 196, 38), pixels)

    if 'Flooring' in farm:
        for tile in farm['Flooring']:
            colourBox(tile.x, tile.y, (50, 50, 50), pixels)

    if 'Fences' in farm:
        for tile in farm['Fences']:
            colourBox(tile.x, tile.y, (200, 200, 200), pixels)

    if 'objects' in farm:
        for tile in farm['objects']:
            name = tile.orientation
            if name == "Weeds":
                colourBox(tile.x, tile.y, (0, 255, 0), pixels)
            elif name == "Stone":
                colourBox(tile.x, tile.y, (125, 125, 125), pixels)
            elif name == "Twig":
                colourBox(tile.x, tile.y, (153, 102, 51), pixels)
            else:
                colourBox(tile.x, tile.y, (255, 0, 0), pixels)

    if 'resourceClumps' in farm:
        for tile in farm['resourceClumps']:
            if tile.type == 672:
                for i in range(tile[3]):
                    for j in range(tile[3]):
                        colourBox(tile.x + i, tile.y + j, (102, 51, 0), pixels)
            elif tile.type == 600:
                for i in range(tile[3]):
                    for j in range(tile[3]):
                        colourBox(tile.x+i, tile.y + j, (75, 75, 75), pixels)
    return image


def regenerateFarmInfo(json_from_db):
    sprite = namedtuple('Sprite', ['name', 'x', 'y', 'w', 'h', 'index', 'type', 'growth', 'flipped', 'orientation'])

    for key in json_from_db.keys():
        for i, item in enumerate(json_from_db[key]):
            json_from_db[key][i] = sprite(*item)
    return json_from_db


def main():
    generateImage(getFarmInfo('./saves/Crono_116230451')).save('farm.png')

if __name__ == '__main__':
    main()
