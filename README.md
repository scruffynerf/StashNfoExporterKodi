# Stash NFO Exporter for Kodi

This Stash plugin adds .nfo file and strm support to allow using Stash organized content with Kodi with no Kodi Addon needed.

An .nfo file defines the metadata, and is also used by other media center/organizers.  The standard is Kodi, but variations exist.
A streaming url file (usually .strm, .m3u or m3u8) lists the streaming url of a file, to allow Stash to play it remotely

Kodi uses strm files (basically the stream URL available from Stash, as a line in a text file), and an .nfo file with the metadata.  
These are read directly by Kodi, and it's all put into Kodi's library.  This is just as if you had the videos in Kodi directly,
except it's streamed from Stash

### Other tools and credit for the giants I stand upon: 
This is based on, and replaces the Kodi helper script by @withoutpants.  All due credit to him for his code skills,
this heavily cribs from it, but turns that into a background running plugin that just keeps NFO files updated,
rather than a single script to run.  Also thanks to stg-annon for his code in general..

### What this is NOT: 
A Kodi Addon that gets all of the info from Stash directly.  An Addon doesn't use your Kodi Library,
it's just a frontend UI for Kodi to talk to Stash.  There are Kodi->Stash addons, where Stash has no code on it's side.  
This is the opposite: Stash code, that makes something Kodi can process, and no code on the Kodi side.  
There is value in each approach, and I'll likely tackle the other side next.

## Installation:

Download (zip or git clone) into a folder in your plugin directory that Stash knows about.  Reload plugins.  Visit the tasks page to enable or disable the plugin (or edit the config file)

### By default:
If your Stash instance url is `'localhost'` or `'127.0.0.1'`, or other non-routable address,
and you need it to be `192.168.1.xxx` or `10.1.x.x` or even Internet accessible, 
you can have this tool replace the local url used with a corrected replacement.  It also will support adding an apikey for access.  
**Warning: if you expose your Stash to the Internet, follow safe practices, you are on your own.**

### Naming: 
Using the stashid (a simple number) is the default.  You can use filename.nfo, if you wish.  Just change the config file

### Location: 
We'll put these files into one directory/folder.  You can share or copy these to your Kodi (or other) setup, and when read, 
they'll reference the Stash instance, and communicate with it to get screenshots/etc (one time load into Kodi),
as well as to play the video via streaming.

You can also choose to store the NFO (and no streaming file) next to the file itself, if you just want to share your media folders,
and have Kodi read them and still have access to Kodi info

### Genre:
If you have a set of Genre tags you wish to use, you can add that to the config, and children of that tag will be consider Genres in NFO metadata.
By default, this is set to Themes (which is the closest tag to Genre on StashDB)

### How to use:
Once the plugin is installed, any new or updated file, by default, only Organized files are processed and a nfo and strm are created.
Either share or copy these to where Kodi can see them, and tell Kodi to process them as Movies with Local Info.
Kodi will load these into its' library, and your Stash videos will be visible.

### Known issues:
Kodi doesn't re-read the .nfo unless you either manually refresh the individual video OR you tell Kodi to forget and reload the data on those files.  Not ideal.

### Potential Issues solved: 
It turns out STRM files shouldn't be written in UTF8 according to Kodi.  It causes a weird error where Kodi complains it can't do 'http' file 
stream urls. It doesn't correct match to "http" due to the UTF8, but it's an invisible error.  
If you use m3u8, we will enable UTF8 writing of that file.

### Image handling: 
It all depends on the Kodi skin and display type you use... there are so many good ones, I encourage you to try different skins and find a 
favorite way to display your content.  Stash doesn't support enough Artwork types (yet), so there are some compromises.
Landscape screenshots are used, but Posters (usually from Movies) take Priority if available.
Performer images are used.  
Studio logos are available, but not well supported by most skins (still looking for a good one).
If/When Stash adds more image support, I'll update this.

### Not done and might work on it:
- Delete old NFO/strm files if name changes or scene is deleted (you can combine with renamerOnUpdate plugin to help with that)
- Make subdirectories, instead of one big directory full.
- Export images for each video (would require separate directories first)

### Not done and no plans to work on it:
- No Country support in NFO metadata

### Config File Defaults:  
see config.py to change your own setup

```
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
filename = "filename"
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
# name of tag that is parent of Genre tags, so we can label Genres. If set to empty ("") only main tags without children will be used as genre
genre_parentname = ""
#
# When should the nfo be generated?
# Possible overwrite values are:
# - "always": will always create/update the nfo (can be destructive of some nfo content if your existing nfo were not generated by this plugin)
# - "new": will only generate the missing nfo (skip if nfo already exists, generate otherwise)
# - "organized": will generate/overwrite an nfo only the the scene is flagged as "organized"
generate_when = "organized"
#
# if set to true, an existing .nfo file is versioned instead of overwritten 
versioning = True
# if set to true, Poster will be written alongside with the NFO (only works if save path is set to "with files")
saveposter = True
# if set to true, only scenes that have a movie linked will generate an nfo
onlymovie = True
```
