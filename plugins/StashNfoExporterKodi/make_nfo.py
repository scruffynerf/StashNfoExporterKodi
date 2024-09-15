import os
import sys
import json
from datetime import datetime
import log

from stash_interface import StashInterface
import config
import requests, filetype

def basename(f):
    f = os.path.normpath(f)
    return os.path.basename(f)

def xmlSafe(text):
    if text:
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    return text

def VersionFile(filename):

    if os.path.isfile(filename):
        log.debug("Version File with filename " + filename)
        # Determine root filename so extension doesn't get longer
        n, e = os.path.splitext(filename)

        # Is e a three-digit integer preceded by a dot
        if len(e) == 4 and e[1:].isdigit():
            num = 1 + int(e[1:])
            root = n
        else:
            num = 0
            root = filename

        # Find the next available file version
        for i in range(num, 1000):

            new_file = "%s.%03d" % (root, i)
            new_file = os.path.dirname(new_file) + '/' + '.' + os.path.basename(new_file)
            log.debug ("New Filename is " + new_file)
            if not os.path.exists(new_file):
                os.rename(filename, new_file)
                return True
        raise RuntimeError("Can't {} {!r}, all names taken".format(vtype, filename))
    return False

def getOutputSTRMFile(scene):
    if config.filename == "filename":
        return os.path.join(config.save_path, "{}.".format(os.path.splitext(basename(scene['files'][0]['path']))[0]) + config.playlist_ext)
    elif config.filename == "stashid":
        sceneID = scene["id"]
        return os.path.join(config.save_path, "{}.".format(sceneID) + config.playlist_ext)
    else:
        log.error("Check your config file.")
# In the follmmm f
def getOutputNFOFile(scene):
    if config.save_path == "with files":
        return os.path.join(os.path.dirname(scene['files'][0]['path']), "{}.nfo".format(os.path.splitext(basename(scene['files'][0]['path']))[0]))
    elif config.filename == "filename":
        return os.path.join(config.save_path, "{}.nfo".format(os.path.splitext(basename(scene['files'][0]['path']))[0]))
    elif config.filename == "stashid":
        sceneID = scene["id"]
        return os.path.join(config.save_path, "{}.nfo".format(sceneID))
    else:
        log.error("Check your config file.")

def getOutputPosterFile(scene):
    if config.save_path == "with files":
        return os.path.join(os.path.dirname(scene['files'][0]['path']), "{}-poster".format(os.path.splitext(basename(scene['files'][0]['path']))[0]))
    else:
        log.error("Check your config file.")

def getPosterExtension(scene):
    posterURL = scene["paths"]["screenshot"]
    log.info(f"testing scene.paths.screenshot: {posterURL}")
    posterURL = URLrewrite(scene["paths"]["screenshot"])
    log.info(f"Fetch content at URL: {posterURL}")
    response = requests.get(posterURL)
    if response.status_code != 200:
        log.error("Couldn't fetch the image - is poster URL correct?")
        return None
    imageType = filetype.guess(response.content)
    if imageType is None:
        log.warning('Cannot guess iamge type! Is poster truly an image?')
        return None
    return imageType

def getSceneTitle(scene):
    if scene["title"] != None and scene["title"] != "":
        return scene["title"]
    return basename(scene['files'][0]['path'])

def getGenreTags():
    if config.genre_parentname != "":
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
        if not results["findTags"]["tags"]:
            log.warning("'genre_parentname' tag not found in stash. Check README & config.")
            return []
        else:
            resultschildren = results["findTags"]["tags"][0]["children"]
            return get_ids(resultschildren)
    else:
        query = """
        {
        findTags(
            tag_filter: {parent_count: {value: 0 , modifier: EQUALS}}
            filter: {per_page: -1}
        ) {
            count
            tags {
            id
            name
            }
        }
        }
        """
        results = stash.graphql_query(query)
        if not results["findTags"]["tags"]:
            log.warning("tags not found in stash. Check README & config.")
            return []
        else:
            resultschildren = results["findTags"]["tags"]
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
            return "#EXTM3U\n#EXTENC: UTF-8\n#EXTINF:" + str(int(scene['files'][0]["duration"])) + "," + getSceneTitle(scene) + "\n" + URLrewrite(scene['paths']["stream"])
        else:
            return "#EXTM3U\n#EXTINF:" + str(int(scene['files'][0]["duration"])) + "," + getSceneTitle(scene) + "\n" + URLrewrite(scene['paths']["stream"])
    else:
        return URLrewrite(scene['paths']["stream"])

def checkmovie(scene):
    if "movies" in scene:
        for mlist in scene["movies"]:
            m = mlist["movie"]
            if "id" in m:
                return True
    return False

def saveposter(scene, poster):
    gotposter = False
    if "movies" in scene:
        for mlist in scene["movies"]:
            m = mlist["movie"]
            if "front_image_path" in m:
                posterurl = m["front_image_path"]
                if posterurl is not None:
                    # We need to rewrite the URL so API key gets properly inserted in case Stash is secured with username and password
                    response = requests.get(URLrewrite(posterurl))
                    if response.status_code != 200:
                        log.error("Couldn't fetch the image - is poster URL correct?")
                        return
                    imageType = filetype.guess(response.content)
                    if imageType is None:
                        log.warning('Cannot guess iamge type! Is poster truly an image?')
                        return
                    save_path = f"{poster}.{imageType.extension}"
                    with open(save_path, 'wb') as f:
                        f.write(response.content)
                    gotposter = True
    # no movie poster, so let's (sadly) include the landscape screenshot as the poster, until we can do better.
    if gotposter == False:
        posterurl = scene['files'][0]['path']["screenshot"]
        # Same goes here, needs to be rewritten with API key
        response = requests.get(URLrewrite(posterurl))
        if response.status_code != 200:
            log.error("Couldn't fetch the image - is poster URL correct?")
            return
        imageType = filetype.guess(response.content)
        if imageType is None:
            log.warning('Cannot guess iamge type! Is poster truly an image?')
            return
        save_path = f"{poster}.{imageType.extension}"
        with open(save_path, 'wb') as f:
            f.write(response.content)
            f.close()


def generateNFO(scene):
    ret = """<?xml version="1.0" encoding="UTF-8" standalone="yes"?>
<!-- Generated by StashNfoExporterKodi plugin on {now} -->
<movie>
    <title>{title}</title>
    <uniqueid type="stash" default="true">{id}</uniqueid>
{stash_ids}
    <mpaa>XXX</mpaa>
    <playcount>{o_counter}</playcount>
    <dateadded>{created_at}</dateadded>
    <premiered>{date}</premiered>
    <userrating>{rating}</userrating>
    <plot>{details}</plot>
    <studio>{studio}</studio>
    <director>{director}</director>
{performers}
{set}
{tags}
{thumbs}
{fanart}
{art}
{genres}
</movie>"""

    allgenres = getGenreTags()
    genres = []

    stash_ids = ""
    for id in scene["stash_ids"]:
        stash_ids = stash_ids + """    <uniqueid type="stashdb" endpoint="{}">{}</uniqueid>\n""".format(id["endpoint"], id["stash_id"])

    tags = ""
    for t in scene["tags"]:
        tags = tags + """    <tag>{}</tag>\n""".format(xmlSafe(t["name"]))
        if t["id"] in allgenres:
            genres.append("    <genre>{}</genre>\n".format(xmlSafe(t["name"])))

    rating = ""
    if scene["rating100"] != None:
        rating = scene["rating100"]

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
        performers = performers + """    <actor>
        <name>{}</name>
        <role></role>
        <order>{}</order>
        <thumb aspect="poster">{}</thumb>
    </actor>\n""".format(xmlSafe(p["name"]), i, xmlSafe(thumb))
        i += 1

    URLpathsScreenshot = URLrewrite(scene["paths"]["screenshot"])
    thumbs = ["""    <thumb aspect="landscape">{}</thumb>""".format(xmlSafe(URLpathsScreenshot))]
    imgType = getPosterExtension(scene)
    outputPosterFile = xmlSafe(URLpathsScreenshot)
    if imgType is not None:        
        thumbs = ["""    <thumb aspect="landscape">{}</thumb>""".format(xmlSafe(URLrewrite(scene["paths"]["screenshot"])))]
    

    set = ""
    director = ""
    gotposter = False

    # this code is really only for one movie:
    # if you have multiple movies, the director and movie data will be only the last one found.
    # Patch accepted if you need more for some weird reason
    if "movies" in scene:
        log.debug(scene["movies"])
        for mlist in scene["movies"]:
            m = mlist["movie"]
            set = """    <set>
        <name>{}</name>
        <index>{}</index>
    </set>""".format(xmlSafe(m["name"]), mlist["scene_index"] or "")
            if "director" in m:
                director = m["director"]
            if "front_image_path" in m:
                poster = m["front_image_path"]
                if poster is not None:
                # if imgType is not None: # We can implement local thumb as well, same as poster
                    thumbs.append("""    <thumb aspect="poster">{}</thumb>""".format(xmlSafe(URLrewrite(poster))))
                    gotposter = True
            if "back_image_path" in m:
                backcover = m["back_image_path"]
                if backcover is not None:
                    # same principal, using imgType we can implement local file
                    thumbs.append("""    <thumb aspect="poster">{}</thumb>""".format(xmlSafe(URLrewrite(backcover))))

    # no movie poster, so let's (sadly) include the landscape screenshot as the poster, until we can do better.
    if gotposter == False:
        thumbs.append("""    <thumb aspect="poster">{}</thumb>""".format(outputPosterFile))

    customart = ["""    <thumb aspect="fanart">{}</thumb>""".format(xmlSafe(URLrewrite(scene["paths"]["screenshot"])))]
    
    
    if logo != "":
        thumbs.append("""    <thumb aspect="clearlogo">{}</thumb>""".format(xmlSafe(URLrewrite(logo))))
        customart.append("""    <thumb aspect="clearlogo">{}</thumb>""".format(xmlSafe(URLrewrite(logo))))

    fanart = """    <fanart>\n    {}\n    </fanart>""".format("\n".join(customart))
    art = """    <art>\n    {}\n    </art>""".format("\n".join(customart))

    ret = ret.format(title = xmlSafe(getSceneTitle(scene)),
                     now = datetime.now(),
                     id = scene["id"],
                     endpoint = scene["id"],
                     stash_ids = stash_ids,
                     o_counter = scene["o_counter"] or "",
                     created_at = scene["created_at"][:10],
                     details = xmlSafe(scene["details"] or ""),
                     rating = rating,
                     date = date,
                     studio = xmlSafe(studio),
                     director = xmlSafe(director),
                     performers = performers,
                     set = set,
                     tags = tags,
                     thumbs = "\n".join(thumbs),
                     fanart = fanart,
                     art = art,
                     genres = "\n".join(genres)
                     )
    ret = ret.replace("\n\n", "\n")
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
    if len(sys.argv) > 1:
        # Loads from argv for testing...
        json_input = json.loads(sys.argv[1])
    else:
        json_input = json.loads(sys.stdin.read())
    stash = StashInterface(json_input["server_connection"])
    sceneID = json_input['args']['hookContext']['id']
    scene = stash.getScene(sceneID)

    if config.onlymovie == True:
        if not checkmovie(scene):
            log.debug("Scene has no movie and onlymovie setting is active. Exiting.")
            sys.exit()

    # For existing nfo, config defines wether to proceed with generation or not...
    nfofilename = getOutputNFOFile(scene)
    log.debug("NFO Filename is "+ nfofilename)
    if (not scene["organized"] and config.generate_when == "organized") or \
       (os.path.exists(nfofilename) and config.generate_when == "new"):
        # Skip generation...
        sys.exit()

    useUTF = True
    # Create Version if enabled
    if config.versioning:
        VersionFile(nfofilename)
    nfo = generateNFO(scene)
    writeFile(nfofilename, nfo, useUTF)

    if (config.save_path == "with files" and config.saveposter == True):
        poster = getOutputPosterFile(scene)
        saveposter(scene, poster)

    if config.save_path != "with files":
        useUTF = False
        # don't write utf8 if it's strm extension, it breaks in Kodi, only use if m3u8
        if config.playlist_ext == "m3u8":
            useUTF = True
        strm = generateSTRM(scene)
        strmfilename = getOutputSTRMFile(scene)
        writeFile(strmfilename, strm, useUTF)

main()
