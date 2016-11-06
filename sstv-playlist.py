#!/usr/bin/env python
# -*- coding: utf-8 -*-
'''generate m3u8 and xspf playlists with your SmoothStreamsTV credentials'''

from getpass import getpass
from json import loads, dumps
from os import path
from urllib.request import urlopen
from urllib.parse import urlencode
from xml.sax.saxutils import escape
import urllib.request
import os.path
import time
import json
import argparse

__appname__ = 'SSTV-playlist'
__author__ = 'A few dudes'
__version__ = '0.4beta'
__license__ = 'MIT'

config = { }

greeting = '''
SmoothStreamsTV playlist generator

Generates .m3u8 and .xspf playlist files with all channels that are airing programming at the execution time. Currently the playlist generates sessions that are valid for about 4 hours. These files are playable in media players and browsers.
'''

class programinfo:
	description = ""
	channel = 0
	channelname = ""
	height = 0
	endtime = ""
	_title = ""
	_category = ""
	_quality = ""
	_language = ""
	
	def get_title(self):
		if len(self._title) == 0:
			return ("none " + self.endtime).strip()
		else:
			return (self._title + " " + self.quality + " " + self.endtime).replace("  ", " ").strip()
	def set_title(self, title):
		self._title = title
		if len(self._category) == 0:
			if title.startswith("NHL") or title.startswith("Champions Hockey"):
				self._category = "Ice Hockey"
			elif title.startswith("UEFA") or title.startswith("EPL") or title.startswith("Premier League") or title.startswith("La Liga") or title.startswith("Bundesliga") or title.startswith("Serie A"):
				self._category = "World Football"
			elif title.startswith("MLB"):
				self._category = "Baseball"
			elif title.startswith("MMA") or title.startswith("UFC"):
				self._category = "Boxing + MMA"
			elif title.startswith("NCAAF") or title.startswith("CFB"):
				self._category = "NCAAF"
			elif title.startswith("ATP"):
				self._category = "Tennis"
			elif title.startswith("WWE"):
				self._category = "Wrestling"
			elif title.startswith("NFL") or title.startswith("NBA"):
				self._category = title.split(" ")[0].replace(":", "").strip()
		elif self._category == "American Football" and title.startswith("NFL"):
			self._category = "NFL"
	title = property(get_title, set_title)
	
	def get_category(self):
		if len(self._category) == 0 and (self.title.lower().find("news") or self.description.lower().find("news")) > -1:
			return "News"
		else:
			return self._category
	def set_category(self, category):
		if category == "tv":
			self._category = ""
		else:
			self._category = category
	category = property(get_category, set_category)
	
	def get_language(self):
		return self._language
	def set_language(self, language):
		if language.upper() == "US":
			self._language = ""
		else:
			self._language = language.upper()
	language = property(get_language, set_language)
	
	def get_quality(self):
		return self._quality
	def set_quality(self, quality):
		if quality.endswith("x1080"):
			self._quality = "1080i"
			self.height = 1080
		elif quality.endswith("x720") or quality.lower() == "720p":
			self._quality = "720p"
			self.height = 720
		elif quality.endswith("x540") or quality.lower() == "hqlq":
			self._quality = "540p"
			self.height = 540
		elif quality.find("x") > 2:
			self._quality = quality
			self.height = int(quality.split("x")[1])
		else:
			self._quality = quality
			self.height = 0
	quality = property(get_quality, set_quality)

	def get_album(self):
		if self._quality.upper() == "HQLQ" and self.channelname.upper().find(" 720P") > -1:
			self._quality = "720p"
		return (self._category + " " + self.quality + " " + self._language).strip()
	album = property(get_album)

def main():

	global config

	try:
		with open('sstv-playlist-config.json') as jsonConfig:
			config = json.load(jsonConfig)
	except:
		print("Invalid config file. Using defaults.")
		config = {
			"quality": 1,
			"checkChannel": True,
			"includeBadChannels": False,
			"httpTimeoutChannel": 1,
			"username": "",
			"password": "",
			"server": "",
			"rtmp": False,
			"service": "",
			"minQuality": 0,
			"guideLookAheadMinutes": 5
		}

	if not "quality" in config or not isinstance(config["quality"], int):
		config["quality"] = 1
	if not "checkChannel" in config:
		config["checkChannel"] = True
	if not "includeBadChannels" in config:
		config["includeBadChannels"] = False
	if not "httpTimeoutChannel" in config or not (isinstance(config["httpTimeoutChannel"], int) or isinstance(config["httpTimeoutChannel"], float)) or config["httpTimeoutChannel"] < 0 or config["httpTimeoutChannel"] > 15:
		config["httpTimeoutChannel"] = 1
	if not "username" in config:
		config["username"] = ""
	if not "password" in config:
		config["password"] = ""
	if not "server" in config:
		config["server"] = ""
	if not "rtmp" in config:
		config["rtmp"] = False
	if not "service" in config:
		config["service"] = ""
	if not "minQuality" in config or not isinstance(config["minQuality"], int) or config["minQuality"] < 0 or config["minQuality"] > 1080:
		config["minQuality"] = 0
	if not "guideLookAheadMinutes" in config or not isinstance(config["guideLookAheadMinutes"], int) or config["guideLookAheadMinutes"] < 0 or config["guideLookAheadMinutes"] > 1440:
		config["guideLookAheadMinutes"] = 5

	parser = argparse.ArgumentParser(description='SmoothStreamsTV Playlist Generator')
	parser.add_argument('-f','--find', help='Only return channels matching text (case insensitive)', required=False, default="")
	parser.add_argument('-q','--minquality', help='Minimum quality (540, 720, 1080)', required=False, type=int, default=config["minQuality"])
	parser.add_argument('-c','--checkchannel', help='Check channels', required=False, default=config["checkChannel"], action="store_true")
	parser.add_argument('--nocheckchannel', help='Do not check channels', required=False, default=config["checkChannel"], action="store_true")
	parser.add_argument('-b','--includebadchannels', help='Include bad channels', required=False, default=config["includeBadChannels"], action="store_true")
	parser.add_argument('-m','--minutes', help='Minutes in the future to generate the guide. Channels are not checked for values greater than 29', required=False, type=int, default=config["guideLookAheadMinutes"])
	parser.add_argument('-s','--server', help='Server to use (deu, dna, dsg)', required=False, default=config["server"])
	parser.add_argument('--rtmp', help='Use RTMP', required=False, default=config["rtmp"], action="store_true")
	parser.add_argument('-v','--version', help='Show version information', required=False, default=False, action="store_true")
	commandLineArgs = vars(parser.parse_args())

	if commandLineArgs["version"]:
		print (__appname__ + "\n" + __version__)
		exit(0)

	config["minQuality"] = commandLineArgs["minquality"]
	config["checkChannel"] = commandLineArgs["checkchannel"] and not commandLineArgs["nocheckchannel"]
	config["includeBadChannels"] = commandLineArgs["includebadchannels"]
	config["guideLookAheadMinutes"] = int(commandLineArgs["minutes"])
	config["server"] = commandLineArgs["server"]
	config["RTMP"] = commandLineArgs["rtmp"]

	if (config["guideLookAheadMinutes"] > 29):
		config["checkChannel"] = False

	servers = {
		'EU Random': 'deu',
		'   DE-Frankfurt': 'deu.de1',
		'   NL-EVO': 'deu.nl2',
		'   NL-i3d': 'deu.nl1',
		'   UK-London': 'deu.uk',
		'US Random': 'dna',
		'   East': 'dnae',
		'   West': 'dnaw',
		'   East-NJ': 'dnae1',
		'   East-VA': 'dnae2',
		'   East-CAN': 'dnae3',
		'   East-CAN2': 'dnae4',
		'Asia': 'dsg'
	}

	services = {
		'Live247': 'view247',
		'Mystreams/Usport': 'viewms',
		'StarStreams': 'viewss',
		'MMA SR+': 'viewmmasr',
		'StreamTVnow': 'viewstvn'
	}

	# If you have not hardcoded your credentials (above), you will be prompted for them on each run.
	if not config["username"] or not config["password"]:
		print(greeting)
		config["username"], config["password"] = getCredentials(config["username"], config["password"])

	if not config["server"] or not config["server"] in list(servers.values()):
		config["server"] = getServer(servers, "dna")
	if not config["service"] or not config["service"] in list(services.values()):
		config["service"] = getService(services, "viewstvn")

	authSign = getAuthSign(config["username"], config["password"])

	print(config)
	print('Generating playlist')

	jsonGuide1 = getJSON("iptv.json", "http://guide.smoothstreams.tv/feed.json", "https://iptvguide.netlify.com/iptv.json")
	jsonGuide2 = getJSON("tv.json", "https://iptvguide.netlify.com/tv.json", "http://199.175.52.89/feed.json")
	generatePlaylists(config["server"], config["RTMP"], config["service"], config["quality"], config["minQuality"], config["guideLookAheadMinutes"], commandLineArgs["find"].lower(), authSign, jsonGuide1, jsonGuide2)

# end main()

def getJSON(sFile, sURL, sURL2):

	try:
		if os.path.isfile(sFile) and time.time() - os.stat(sFile).st_mtime < 7200:
			retVal = json.loads(open(sFile, 'r').read())
			return retVal
	except:
		pass

	try:
		sJSON = urllib.request.urlopen(sURL).read().decode("utf-8")
		retVal = json.loads(sJSON)
	except:
		try:
			sJSON = urllib.request.urlopen(sURL2).read().decode("utf-8")
			retVal = json.loads(sJSON)
		except:
			return json.loads("{}")

	file = open(sFile, "w+")
	file.write(sJSON)
	file.close()
	return retVal

# end getJSON()

def getAuthSign(un, pw):
	'''request JSON from server and return hash'''

	url = 'http://smoothstreams.tv/schedule/admin/dash_new/hash_api.php?' + urlencode({ "username": un, "password": pw, "site": config["service"] })

	try:
		response = urlopen(url).read().decode('utf-8')
		data = loads(response)
		if data['hash']:
			return data['hash']

	except ValueError:
		print('Unable to retrieve data from the server.\nPlease check your internet connection and try again.')
		exit(1)
	except KeyError:
		print('There was an error with your credentials.\nPlease double-check your username and password and try again.')
		exit(1)
# end getAuthSign()


def getCredentials(oldUser, oldPass):
	'''prompt user for username and password'''

	print('You may wish to store your credentials and server preferences in this file by opening it in a text editor and filling in the username, password, and server fields. If you choose not to do this, you will be prompted for this information on each run of this script.')

	print('\nPlease enter your username for SmoothStreamsTV:')
	username = input(oldUser)
	print('\nThank you, ' + username + '.\n')

	print('\nPlease enter your password for SmoothStreamsTV:')
	password = getpass(oldPass)

	return username, password
# end getCredentials()


def getServer(servers, defServer):
	'''prompt user to choose closest server'''

	validServer = False

	print('\nServer options:')
	print(dumps(servers, sort_keys=True, indent=4))
	print('Example, for US West enter "dnaw" (without the quotes)\n')
	print('\nPlease choose your server:')
	server = input(defServer)
	if not server:
		server = defServer
	if not server in list(servers.values()):
		print('\n"' + server + '" is not a recognized server. The playlist will be built with "' + defServer + '", but may not work as expected.\n')
		server = defServer

	return (server)
# end getServer()


def getService(services, defService):
	'''prompt user to choose service'''

	validService = False

	print('\nService options:')
	print(dumps(services, sort_keys=True, indent=4))
	print('Example, for StreamTVnow enter "viewstvn" (without the quotes)\n')
	print('\nPlease choose your service:')
	service = input(defService).lower()
	if not service:
		service = defService
	if not service in list(services.values()):
		print('\n"' + service + '" is not a recognized service. The playlist will be built with "' + defService + '", but may not work as expected.\n')
		service = defService

	return (service)
# end getService()


def buildPlaylistFile(fileName, body):
	'''write playlist to a new local m3u8 file'''

	# open file to write, or create file if DNE, write <body> to file and save
	with open(fileName, 'w+') as f:
		f.write(body)
		f.close()

	# check for existence/closure of file
	if f.closed:
		print('Playlist built successfully, located at: ' + path.abspath(fileName))
	else:
		raise FileNotFoundError

# end buildPlaylistFile()


def generatePlaylists(server, rtmp, service, streamQuality, minQuality, guideLookAheadMinutes, find, authSign, jsonGuide1, jsonGuide2):
	'''build strings of channels in m3u8 and xspf formats'''

	if rtmp:
		urlTemplate = 'rtmp://{0}.smoothstreams.tv:3625/{1}?wmsAuthSign={4}/ch{2}q{3}.stream'
	else:
		urlTemplate = 'http://{0}.smoothstreams.tv:9100/{1}/ch{2}q{3}.stream/playlist.m3u8?wmsAuthSign={4}=='
	m3u8TrackTemplate = '#EXTINF:-1,{0} - {1} #{2}\n{3}\n{4}\n'
	xspfBodyTemplate = ('<?xml version="1.0" encoding="UTF-8"?>\n' +
		 '<playlist xmlns="http://xspf.org/ns/0/" xmlns:vlc="http://www.videolan.org/vlc/playlist/ns/0/" version="1">\n' +
		'\t<title>Playlist</title>\n' +
		'\t<trackList>\n' +
		'{0}' +
		'\t</trackList>\n' +
		'\t<extension application="http://www.videolan.org/vlc/playlist/0">\n' +
		'{1}' +
		'\t</extension>\n' +
		'</playlist>')
	xspfTrackTemplate = ('\t\t<track>\n' +
		'\t\t\t<location>{5}</location>\n' +
		'\t\t\t<title>{3}</title>\n' +
		'\t\t\t<creator>Ch{4} {8}</creator>\n' +
		'\t\t\t<album>{0}</album>\n' +
		'\t\t\t<trackNum>{6}</trackNum>\n' +
		'\t\t\t<annotation>{9}</annotation>\n' +
		'\t\t\t<extension application="http://www.videolan.org/vlc/playlist/0">\n' +
		'\t\t\t\t<vlc:id>{7}</vlc:id>\n' +
		'\t\t\t</extension>\n' +
		'\t\t</track>\n')
	xspfTrack2Template = '\t\t<vlc:item tid="{0}"/>\n'
	m3u8 = '#EXTM3U\n'
	xspfTracks = ""
	xspfTracks2 = ""
	trackCounter = 0
	foundChannels = 0

	maxChannel = 0
	for item, x in iter(jsonGuide1.items()):
		if int(item) > maxChannel:
			maxChannel = int(item)
	for item, x in iter(jsonGuide2.items()):
		if int(item) > maxChannel:
			maxChannel = int(item)

	# iterate through channels in channel-number order
	for channel in range(1, maxChannel):
		program = getProgram(jsonGuide1, jsonGuide2, channel, time.localtime(time.time() + guideLookAheadMinutes * 60))
		url = urlTemplate.format(server, service, format(channel, "02"), str(streamQuality), authSign)
		print('\r' + str(channel) + "/" + str(maxChannel), end='')
		if (len(find) == 0 or program.title.lower().find(find) > -1):
			chanResp = checkChannelURL(channel, url)
			if (config["includeBadChannels"] or chanResp.find("#EXT-X-VERSION:") > 0):
				if chanResp.find("RESOLUTION=") > -1:
					program.quality = chanResp.split("RESOLUTION=")[1].split(",")[0].split("\n")[0]
				if not minQuality or program.height == 0 or minQuality < 360 or minQuality <= program.height:
					m3u8 += m3u8TrackTemplate.format(program.album, program.title, str(program.channel), program.description, url)
					xspfTracks += xspfTrackTemplate.format(escape(program.album), escape(program.quality), escape(program.language), escape(program.title), str(program.channel), url, str(trackCounter + 1), str(trackCounter), escape(program.channelname), escape(program.description))
					xspfTracks2 += xspfTrack2Template.format(str(trackCounter))
					foundChannels += 1
		trackCounter = trackCounter + 1
	print()

	if (foundChannels == 0):
		print("No channels found")
	else:
		print(str(foundChannels) + " channels found")
		xspf = xspfBodyTemplate.format(xspfTracks, xspfTracks2)
		buildPlaylistFile("SmoothStreamsTV.xspf", xspf)
		buildPlaylistFile("SmoothStreamsTV.m3u8", m3u8)
# generatePlaylists()

def getProgram(jsonGuide1, jsonGuide2, channel, tmNow):

	retVal = programinfo()
	try:
		oChannel = jsonGuide1[str(int(channel))]
		retVal.channel = channel
		retVal.channelname = oChannel["name"].replace(format(channel, "02") + " - ", "").strip()
		for item in oChannel["items"]:
			startTime = time.strptime(item["time"], '%Y-%m-%d %H:%M:%S')
			endTime = time.strptime(item["end_time"], '%Y-%m-%d %H:%M:%S')
			if startTime < tmNow and endTime > tmNow:
				retVal.category = item["category"].strip()
				retVal.quality = item["quality"].upper()
				retVal.language = item["language"].upper()
				retVal.title = item["name"].strip()
				retVal.description = item["description"].strip()
				retVal.channel = channel
				retVal.endtime = time.strftime("%H:%M", startTime) + "-" + time.strftime("%H:%M", endTime)
				return retVal

		oChannel = jsonGuide2[str(int(channel))]
		for item in oChannel["items"]:
			startTime = time.strptime(item["time"], '%Y-%m-%d %H:%M:%S')
			endTime = time.strptime(item["end_time"], '%Y-%m-%d %H:%M:%S')
			if startTime < tmNow and endTime > tmNow:
				retVal.category = item["category"].strip()
				retVal.quality = item["quality"].upper()
				retVal.language = item["language"].upper()
				retVal.title = item["name"].strip()
				retVal.description = item["description"].strip()
				retVal.channel = channel
				retVal.endtime = time.strftime("%H:%M", startTime) + "-" + time.strftime("%H:%M", endTime)
				return retVal
	except:
		return retVal

	return retVal
# end getProgram

def checkChannelURL(channel, sURL):
	if not config["checkChannel"]:
		return "#EXTM3U\n#EXT-X-VERSION:3"
	
	try:
		return urlopen(sURL, timeout = config["httpTimeoutChannel"]).read().decode('utf-8')
	except:
		return ""
# checkChannelURL()

if __name__ == '__main__':
	main()
