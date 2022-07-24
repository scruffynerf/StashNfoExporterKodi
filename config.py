# if needed for remote access, add your stash api_key
api_key = ""
#
# we use the built in plugin access to talk to your stash, this is for search/replacement in URLs
# substitute the replacement for the server url, if they are different
server_url = "http://localhost:9999"
replacement_server_url = "http://localhost:9999"
#
# Where should we save the nfo and playlist files?
# If you put "with files", we will save a .nfo with the video files, named the same, and will make NO playlist file
# Otherwise, put a path here to save into... /home/user/kodistashfiles or C:\kodistashfiles
save_path = "with files"
#
# filenaming options: stashid or filename?  stashid (a number) is cleaner, and sure to be updated (and not orphaned), even if the filename changes.
# if you set the above to "with files", it'll force filename anyway, to match the filename.
filename = "stashid"
#
# name of playlist file extension
# choices: strm, or m3u, or m3u8
playlist_ext = "strm"
#
# use extended playlist (extm3u) info?
# This works in Kodi, and ensures the scene name appears in Kodi playlist, otherwise it just says 'stream'
# Use false if you are using some non-Kodi application that doesn't support it, and you just want a pure URL strm file.
m3u = True
#
# name of tag that is parent of Genre tags, so we can label Genres
genre_parentname = "Themes"
#
# Only do for Organized Files?
organized_only = True
