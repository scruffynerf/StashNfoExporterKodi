import os
import sys
import json
import log

from stash_interface import StashInterface
import config

def basename(f):
    f = os.path.normpath(f)
    return os.path.basename(f)

def getOutputSTRMFile(scene):
    if config.filename == "filename":
       return os.path.join(config.save_path, "{}.".format(os.path.splitext(basename(scene["path"]))[0]) + config.playlist_ext)
    elif config.filename == "stashid":
       sceneID = scene["id"]
       return os.path.join(config.save_path, "{}.".format(sceneID) + config.playlist_ext)
    else:
      log.error("Check your config file.")

def getOutputNFOFile(scene):
    if config.filename == "filename":
       return os.path.join(config.save_path, "{}.nfo".format(os.path.splitext(basename(scene["path"]))[0]))
    elif config.save_path == "with files":
       return os.path.join(os.path.dirname(scene["path"]), "{}.nfo".format(os.path.splitext(basename(scene["path"]))[0]))
    elif config.filename == "stashid":
       sceneID = scene["id"]
       return os.path.join(config.save_path, "{}.nfo".format(sceneID))
    else:
      log.error("Check your config file.")

def getSceneTitle(scene):
    if scene["title"] != None and scene["title"] != "":
        return scene["title"]
    return basename(scene["path"])

def getGenreTags():
    query = """
    {
      findTags(
        tag_filter: {name: {value: """ + '"' + config.genre_parentname + '"' + """ , modifier: EQUALS}}
        filter: {per_page: -1}
      ) {
        count
        tags {
          id
          name
          children {
            name
            id
          }
        }
      }
    }
    """
    results = stash.graphql_query(query)
    resultschildren = results["findTags"]["tags"][0]["children"]
    return get_ids(resultschildren)

def get_ids(obj):
    ids = []
    for item in obj:
        ids.append(item['id'])
    return ids

def URLrewrite(url):
    if config.replacement_server_url:
       url = url.replace(config.server_url, config.replacement_server_url)
    if config.api_key:
        return url + "&apikey=" + config.api_key
    return url

def generateSTRM(scene):
    if config.m3u:
       if config.playlist_ext == "m3u8":
         return "#EXTM3U\n#EXTENC: UTF-8\n#EXTINF:" + str(int(scene["file"]["duration"])) + "," + getSceneTitle(scene) + "\n" + URLrewrite(scene["paths"]["stream"])
       else:
         return "#EXTM3U\n#EXTINF:" + str(int(scene["file"]["duration"])) + "," + getSceneTitle(scene) + "\n" + URLrewrite(scene["paths"]["stream"])
    else:
       return URLrewrite(scene["paths"]["stream"])

def generateNFO(scene):
    ret = """<?xml version="1.0" encoding="UTF-8" standalone="yes" ?>
    <movie>
    <title>{title}</title>
    <uniqueid type="stash">{id}</uniqueid>
    <premiered>{date}</premiered>
    <userrating>{rating}</userrating>
    <plot>{details}</plot>
    <studio>{studio}</studio>
    <director>{director}</director>
    {performers}
    {tags}
    {thumbs}
    {fanart}
    {genres}
    </movie>
    """

    allgenres = getGenreTags()
    genres = []

    tags = ""
    for t in scene["tags"]:
        tags = tags + """<tag>{}</tag>""".format(t["name"])
        if t["id"] in allgenres:
           genres.append("<genre>{}</genre>".format(t["name"]))

    rating = ""
    if scene["rating"] != None:
        rating = scene["rating"]

    date = ""
    if scene["date"] != None:
        date = scene["date"]

    studio = ""
    logo = ""
    if scene["studio"] != None:
        studio = scene["studio"]["name"]
        logo = scene["studio"]["image_path"]
        if not logo.endswith("?default=true"):
            logo = URLrewrite(logo)
        else:
            logo = ""

    performers = ""
    i = 0
    for p in scene["performers"]:
        thumb = URLrewrite(p["image_path"])
        performers = performers + """<actor>
        <name>{}</name>
        <role></role>
        <order>{}</order>
        <thumb aspect="actor">{}</thumb></actor>""".format(p["name"], i, thumb)
        i += 1

    thumbs = ["""<thumb aspect="landscape">{}</thumb>""".format(URLrewrite(scene["paths"]["screenshot"]))]

    director = ""
    gotposter = False

    # this code is really only for one movie:
    # if you have multiple movies, the director will be the last director only.
    # Patch accepted if you need more for some weird reason
    if "movies" in scene:
       log.debug(scene["movies"])
       for mlist in scene["movies"]:
          m = mlist["movie"]
          if "director" in m:
             director = m["director"]
          if "front_image_path" in m:
             poster = m["front_image_path"]
             if poster is not None:
                thumbs.append("""<thumb aspect="poster">{}</thumb>""".format(URLrewrite(poster)))
                gotposter = True
          if "back_image_path" in m:
             backcover = m["back_image_path"]
             if backcover:
                thumbs.append("""<thumb aspect="poster2">{}</thumb>""".format(URLrewrite(backcover)))

    # no movie poster, so let's (sadly) include the landscape screenshot as the poster, until we can do better.
    if gotposter == False:
       thumbs.append("""<thumb aspect="poster">{}</thumb>""".format(URLrewrite(scene["paths"]["screenshot"])))

    fanart = ["""<thumb aspect="fanart">{}</thumb>""".format(URLrewrite(scene["paths"]["screenshot"]))]

    if logo != "":
        thumbs.append("""<thumb aspect="clearlogo">{}</thumb>""".format(URLrewrite(logo)))
        fanart.append("""<thumb aspect="clearlogo">{}</thumb>""".format(URLrewrite(logo)))

    fanart = """<fanart>{}</fanart>""".format("\n".join(fanart))

    ret = ret.format(title = getSceneTitle(scene),
                     id = scene["id"],
                     details = scene["details"] or "",
                     rating = rating,
                     date = date,
                     studio = studio,
                     director = director,
                     performers = performers,
                     tags = tags,
                     thumbs = "\n".join(thumbs),
                     fanart = fanart,
                     genres = "\n".join(genres)
                     )
    return ret

def writeFile(fn, data, useUTF=False):
    encoding = None
    if useUTF:
        encoding = "utf-8-sig"
    os.makedirs(os.path.dirname(fn), exist_ok=True)
    f = open(fn, "w", encoding=encoding)
    f.write(data)
    f.close()

def main():
    global stash
    json_input = json.loads(sys.stdin.read())
    stash = StashInterface(json_input["server_connection"])
    sceneID = json_input['args']['hookContext']['id']
    scene = stash.getScene(sceneID)

    if ( (config.organized_only is True) and (scene["organized"] is False) ):
      sys.exit()

    useUTF = True
    nfo = generateNFO(scene)
    nfofilename = getOutputNFOFile(scene)
    writeFile(nfofilename, nfo, useUTF)

    if config.save_path != "with files":
      useUTF = False
      # don't write utf8 if it's strm extension, it breaks in Kodi, only use if m3u8
      if config.playlist_ext == "m3u8":
         useUTF = True
      strm = generateSTRM(scene)
      strmfilename = getOutputSTRMFile(scene)
      writeFile(strmfilename, strm, useUTF)

main()
