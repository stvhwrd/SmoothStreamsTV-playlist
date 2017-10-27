![Build Status](https://travis-ci.org/stvhwrd/SmoothStreamsTV-playlist.png)


## Requirements

*   [Python 3.5.2](https://www.python.org/download/releases/3.5.2)<sup>+<sup>

I've made an effort to use only built-in Python modules, but please let me know if your system requires any extra items installed to make this work.


## Instructions

1.  [Download](https://github.com/stvhwrd/SmoothStreamsTV-playlist/archive/master.zip) this repository.

2.  Unzip the zip file.

3.  Open the folder.

4.  Run the script with **Python 3**:  `python3 ./sstv-playlist.py`


## Result

The m3u8 playlist file will be created in the directory that the script is **called from**.

For example, if you are in your home directory,
```bash
$ cd ~
```

and call the script in your `~/Scripts` directory,
```bash
$ python3 ~/Scripts/sstv-playlist.py
```

the script will be created in your home directory.
```bash
$ ls ~

  SmoothStreamsTV.m3u8
```

### Note: the SmoothStreams server provides an access token that is valid for only 240 minutes (4 hours) so this script will need to be run every 4 hours if used in some kind of server configuration.


## Testing

#### Tested on:
*   Mac OS X 10.11
*   macOS 10.12
*   Ubuntu 14.04.5 LTS
*   Ubuntu 16.04.1 LTS
*   Windows 10


## Notable Forks

Some people have built some cool stuff off of this script.  Here are a couple that I know of:

*   [stankness on BitBucket](https://bitbucket.org/stankness/sstv-playlist)
*   [bradmurray on GitHub](https://github.com/bradmurray/SmoothStreamsTV-playlist)


## Feedback

If you have any issues with the program, please be sure to [open an Issue](https://github.com/stvhwrd/SmoothStreamsTV-playlist/issues/new) on GitHub, so that it can be tracked and addressed formally.

A few people have sent me emails, and while I *really* appreciate the feedback, emails can get lost or buried.
GitHub Issues will stick with the project, and are the best way to ensure that the issue is resolved.

Thank you to everyone who has given me feedback on this project!  Please Star or Watch the repo to stay updated.
