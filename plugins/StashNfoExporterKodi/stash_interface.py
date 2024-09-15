import requests
import sys
import re
import log

class StashInterface:
    port = ""
    url = ""
    headers = {
        "Accept-Encoding": "gzip, deflate, br",
        "Content-Type": "application/json",
        "Accept": "application/json",
        "Connection": "keep-alive",
        "DNT": "1"
    }
    cookies = {}

    def __init__(self, conn, fragments={}):
        self.port = conn['Port']
        scheme = conn['Scheme']

        # Session cookie for authentication
        self.cookies = {
            'session': conn.get('SessionCookie').get('Value')
        }

        domain = conn.get('Host') or 'localhost'
        if domain == "0.0.0.0":
            domain = "localhost"

        # Stash GraphQL endpoint
        self.url = scheme + "://" + domain + ":" + str(self.port) + "/graphql"
        log.debug(f"Using stash GraphQl endpoint at {self.url}")

        self.fragments = fragments
        self.fragments.update(stash_gql_fragments)

    def __resolveFragments(self, query):

        fragmentRefrences = list(set(re.findall(r'(?<=\.\.\.)\w+', query)))
        fragments = []
        for ref in fragmentRefrences:
            fragments.append({
                "fragment": ref,
                "defined": bool(re.search("fragment {}".format(ref), query))
            })

        if all([f["defined"] for f in fragments]):
            return query
        else:
            for fragment in [f["fragment"] for f in fragments if not f["defined"]]:
                if fragment not in self.fragments:
                    raise Exception(f'GraphQL error: fragment "{fragment}" not defined')
                query += self.fragments[fragment]
            return self.__resolveFragments(query)

    def __callGraphQL(self, query, variables=None):

        query = self.__resolveFragments(query)

        json = {'query': query}
        if variables is not None:
            json['variables'] = variables

        response = requests.post(self.url, json=json, headers=self.headers, cookies=self.cookies)

        if response.status_code == 200:
            result = response.json()
            if result.get("errors", None):
                for error in result["errors"]:
                    raise Exception("GraphQL error: {}".format(error))
            if result.get("data", None):
                return result.get("data")
        elif response.status_code == 401:
            sys.exit("HTTP Error 401, Unauthorised. Cookie authentication most likely failed")
        else:
            raise ConnectionError(
                "GraphQL query failed:{} - {}. Query: {}. Variables: {}".format(
                    response.status_code, response.content, query, variables)
            )

    def graphql_query(self, query, variables=None):
        return self.__callGraphQL(query, variables)

    def get_scenes_id(self, filter={}):
        query = """
        query FindScenes($filter: FindFilterType, $scene_filter: SceneFilterType, $scene_ids: [Int!]) {
            findScenes(filter: $filter, scene_filter: $scene_filter, scene_ids: $scene_ids) {
                count
                scenes {
                    id
                }
            }
        }
        """
        variables = {
            "filter": { "per_page": -1 },
            "scene_filter": filter
        }

        result = self.__callGraphQL(query, variables)
        scene_ids = [s["id"] for s in result.get('findScenes').get('scenes')] 

        return scene_ids

    def update_scene(self, scene_data):
        query = """
            mutation SceneUpdate($input:SceneUpdateInput!) {
                sceneUpdate(input: $input) {
                    id
                }
            }
        """
        variables = {'input': scene_data}

        result = self.__callGraphQL(query, variables)
        return result["sceneUpdate"]["id"]

    def get_root_paths(self):
        query = """
            query Configuration {
                configuration {
                    general{
                        stashes{
                            files{
                                path
                            }
                            excludeVideo
                        }
                    }
                }
            }
        """
        result = self.__callGraphQL(query)

        stashes = result["configuration"]["general"]["stashes"]
        paths = [s["path"] for s in stashes if not s["excludeVideo"]] 

        return paths

    def getScene(self, scene_id):
        query = """
    query FindScene($id: ID!, $checksum: String) {
        findScene(id: $id, checksum: $checksum) {
            ...SceneData
        }
    }
    fragment SceneData on Scene {
        id
        title
        details
        url
        date
        o_counter
        organized
        interactive
        rating100
        director
        created_at
        files {
            path
            size
            duration
            video_codec
            audio_codec
            width
            height
            frame_rate
            bit_rate
        }
        paths {
            screenshot
            preview
            stream
            webp
            vtt
            sprite
            funscript
        }
        scene_markers {
            ...SceneMarkerData
        }
        galleries {
            ...SlimGalleryData
        }
        studio {
            ...SlimStudioData
        }
        movies {
            movie {
                ...MovieData
            }
            scene_index
        }
        tags {
            ...SlimTagData
        }
        performers {
            ...PerformerData
        }
        stash_ids {
            endpoint
            stash_id
        }
    }
    fragment SceneMarkerData on SceneMarker {
        id
        title
        seconds
        stream
        preview
        screenshot
        scene {
            id
        }
        primary_tag {
            id
            name
            aliases
        }
        tags {
            id
            name
            aliases
        }
    }
    fragment SlimGalleryData on Gallery {
        id
        files {
            path
        }
        title
        date
        url
        details
        organized
        image_count
        cover {
            files {
                size
                width
                height
            }
            paths {
                thumbnail
            }
        }
        studio {
            id
            name
            image_path
        }
        tags {
            id
            name
        }
        performers {
            id
            name
            gender
            favorite
            image_path
        }
        scenes {
            id
            title
            files {
                path
            }
        }
    }
    fragment SlimStudioData on Studio {
        id
        name
        image_path
        stash_ids {
            endpoint
            stash_id
        }
        parent_studio {
            id
        }
        details
        aliases
    }
    fragment MovieData on Movie {
        id
        name
        aliases
        duration
        date
        director
        studio {
            ...SlimStudioData
        }
        synopsis
        url
        front_image_path
        back_image_path
        scene_count
        scenes {
            id
            title
            files{
                path
            }
        }
    }
    fragment SlimTagData on Tag {
        id
        name
        aliases
        image_path
    }
    fragment PerformerData on Performer {
        id
        name
        url
        gender
        twitter
        instagram
        birthdate
        ethnicity
        country
        eye_color
        height_cm
        measurements
        fake_tits
        career_length
        tattoos
        piercings
        alias_list
        favorite
        image_path
        scene_count
        image_count
        gallery_count
        movie_count
        tags {
            ...SlimTagData
        }
        stash_ids {
            stash_id
            endpoint
        }
        details
        death_date
        hair_color
        weight
    }
    """
        variables = {
            "id": scene_id
        }
        result = self.__callGraphQL(query, variables)
        if result:
            return result.get('findScene')
        return None

stash_gql_fragments = {}
