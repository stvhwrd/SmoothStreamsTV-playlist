#!/usr/bin/env python3
# -*- coding: utf-8 -*-

'''generate an m3u8 playlist with your SmoothStreamsTV credentials'''

import argparse
from getpass import getpass
from json import loads, dumps
from os import path, environ
from urllib.request import urlopen
from urllib.parse import urlencode
import time

__appname__ = 'SSTV-playlist'
__author__ = 'Stevie Howard (stvhwrd)'
__copyright__ = 'Copyright 2016, Stevie Howard'
__license__ = 'MIT'
__version__ = 'v0.2-beta'


greeting = '''
WELCOME to the SmoothStreamsTV playlist generator!

This program will generate an .m3u8 playlist file with all available channels
for the SmoothStreamsTV IPTV provider, playable in media players and browsers.
Please note: server and channel names/numbers are sourced from SmoothStreamsTV,
and current as of October 3, 2018.
'''


def main():

    # example: username = 'sampleuser@email.com'
    username = ''
    # example: password = 'psswrd1234!'
    password = ''
    # example for US West:  server = 'dnaw'
    server = ''
    # example for StreamTVNow:  host = 'viewstvn'
    host = ''

    # Parse any arguments provided at runtime
    parser = argparse.ArgumentParser()
    parser.add_argument('-e', '--env', help='run the script using environment variables exclusively.', action='store_true')
    args = parser.parse_args()

    # This is specifically for integration testing with Travis CI,
    # but could be used by anyone who cares to set environment variables.
    if args.env:
        print("\nLooking for environment variables...")
        try:
            username = environ['SSTV_USERNAME']
            if username:
                print("SSTV_USERNAME set.")
        except KeyError:
            print('SSTV_USERNAME environment variable not found.')

        try:
            password = environ['SSTV_PASSWORD']
            if password:
                print("SSTV_PASSWORD set.")
        except KeyError:
            print('SSTV_PASSWORD environment variable not found')

        try:
            server = environ['SSTV_SERVER']
            if server:
                print("SSTV_SERVER set.")
        except KeyError:
            print('SSTV_SERVER environment variable not found')

        try:
            host = environ['SSTV_HOST']
            if host:
                print("SSTV_HOST set.")
        except KeyError:
            print('SSTV_HOST environment variable not found')


    colourPrint('bold', greeting)

    servers = {
        'Asia Random':                          'dap',
        'Europe Random':                        'deu',
        'Europe Germany Random':                'deu-de',
        'Europe Netherlands Random':            'deu-nl',
        'Europe Netherlands 1 (i3d)':           'deu-nl1',
        'Europe Netherlands 2 (i3d)':           'deu-nl2',
        'Europe Netherlands 3 (Amsterdam)':     'deu-nl3',
        'Europe Netherlands 4 (Breda)':         'deu-nl4',
        'Europe Netherlands 5 (Enschede)':      'deu-nl5',
        'Europe United Kingdom Random':         'deu-uk',
        'Europe United Kingdom 1 (io)':         'deu-uk1',
        'Europe United Kingdom 2 (100TB)':      'deu-uk2',
        'North America Random':                 'dna',
        'North America East Random':            'dnae',
        'North America East 1 (New York)':      'dnae1',
        'North America East 2 (Virginia)':      'dnae2',
        'North America East 3 (Quebec)':        'dnae3',
        'North America East 4 (Georgia)':       'dnae4',
        'North America East 6 (New York)':      'dnae6',
        'North America West Random':            'dnaw',
        'North America West 1 (Arizona)':       'dnaw1',
        'North America West 2 (California)':    'dnaw2',
        'North America West 3 (Illinois)':      'dnaw3',
        'North America West 4 (Illinois II)':   'dnaw4',
    }

    hosts = {
        'Live247':        'view247',
        'MMA-TV/MyShout': 'viewmmasr',
        'MyStreams':      'viewms',
        'StarStreams':    'viewss',
        'StreamTVNow':    'viewstvn',

    }

    # If you have not hardcoded your credentials and server/host preferences
    # above, you will be prompted for them on each run of the script.

    if not host or not server or not username or not password:
        colourPrint('bold',
            ('You may wish to store your credentials and server ' +
                'preferences in this file by opening it in a text editor ' +
                'and filling in the username, password, host, and server ' +
                'fields.\nIf you choose not to do this, you will be ' +
                'prompted for this information on each run of this script.'))

    if not host:
        host = getHost(hosts)

    if not server:
        server = getServer(servers)

    if not username or not password:
        hostName = list(hosts.keys())[list(hosts.values()).index(host)]
        username, password = getCredentials(hostName)

    authSign = getAuthSign(username, password, host)

    playlistText = generatePlaylist(server, host, authSign)

    colourPrint('yellow',
                '\nPlease wait, generating playlist.')

    buildPlaylistFile(playlistText)

    exit


def getAuthSign(username, password, host):
    '''request JSON from server and return hash'''

    baseUrl = 'http://auth.smoothstreams.tv/hash_api.php?'

    params = {
        "username": username,
        "password": password,
        "site": host
    }

    url = baseUrl + urlencode(params)

    try:
        response = urlopen(url).read().decode('utf-8')
        data = loads(response)
        if data['hash']:
            colourPrint('green',
                        '\nThank you, authentication successful.\n')
            return data['hash']

    except ValueError:
        colourPrint('red',
                    'Unable to retrieve data from the server.\n' +
                    'Please check your internet connection and try again.')
        exit(1)
    except KeyError:
        colourPrint('red',
                    'There was an error with your credentials.\n' +
                    'Please double-check your username and password,' +
                    ' and try again.')
        main()


def getCredentials(hostName):
    '''prompt user for username and password'''

    colourPrint('yellow',
                '\nPlease enter your username for ' + hostName + ':')
    username = input('')
    colourPrint('green',
                '\nThank you, ' + username + '.\n')

    colourPrint('yellow',
                '\nPlease enter your password for ' + hostName + ':')
    password = getpass('')

    return username, password


def getServer(servers):
    '''prompt user to choose closest server'''

    colourPrint('yellow',
                '\nServer options:')
    colourPrint('yellow',
                dumps(servers, sort_keys=False, indent=4))
    print('Example - for North America Random, enter: dna\n')
    colourPrint('yellow',
                '\nPlease choose your server:')
    server = input('')

    if server in servers.values():
        # Get key from value in dictionary
        serverName = list(servers.keys())[list(servers.values()).index(server)]
        colourPrint('green',
                    '\nYou have chosen the ' + serverName + ' server.\n')
        return (server)

    else:
        colourPrint('red',
                    '\n"' + server + '" is not a recognized server.\n' +
                     'Please run the script again and choose a valid server.')
        exit(1)


def getHost(hosts):
    '''prompt user to choose closest server'''

    colourPrint('yellow',
                '\nHost options:')
    colourPrint('yellow',
                dumps(hosts, sort_keys=False, indent=4))
    print('Example, for StreamTVNow: enter "viewstvn" (without the quotes)\n')
    colourPrint('yellow',
                '\nPlease choose your host:')
    host = input('')

    if host in hosts.values():
        # Get key from value in dictionary
        hostName = list(hosts.keys())[list(hosts.values()).index(host)]
        colourPrint('green',
                    '\nYou have chosen the ' + hostName + ' host.\n')
        return (host)
    else:
        colourPrint('red',
                    '\n"' + host + '" is not a recognized host.\n' +
                     'Please run the script again and choose a valid host.')
        exit(1)


def buildPlaylistFile(body):
    '''write playlist to a new local m3u8 file'''

    title = 'SmoothStreamsTV.m3u8'

    # open file to write, or create file if DNE, write <body> to file and save
    with open(title, 'w+') as f:
        f.write(body)
        f.close()

    # check for existence/closure of file
    if f.closed:
        colourPrint('yellow',
                    '\nPlaylist built successfully, located at: ')
        colourPrint('underline',
                    path.abspath(title))
        exit(0)
    else:
        raise FileNotFoundError
    return


def generatePlaylist(server, host, authSign):
    '''build string of channels in m3u8 format based on
    global channelDictionary'''

    m3u8_playlist = '#EXTM3U\n'
    # iterate through channels in channel-number order
    for channel in sorted(channelDictionary, key=lambda channel: int(channel)):
        m3u8_playlist += ('#EXTINF:-1, ' + channel + ' ' + channelDictionary[channel] +
            '\n' + 'https://' + server + '.smoothstreams.tv/' + host + '/ch' + channel +
            'q1.stream/playlist.m3u8?wmsAuthSign=' + authSign + '\n')

    return m3u8_playlist

class colour:
    PURPLE = '\033[95m'
    CYAN = '\033[96m'
    DARKCYAN = '\033[36m'
    BLUE = '\033[94m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BOLD = '\033[1m'
    UNDERLINE = '\033[4m'
    END = '\033[0m'


def colourPrint(spec, text):
    '''print text with specified formatting effect'''

    text = str(text)
    if spec.upper() == 'BOLD':
        print((colour.BOLD + text + colour.END))
    elif spec.upper() == 'GREEN':
        print((colour.GREEN + text + colour.END))
    elif spec.upper() == 'YELLOW':
        print((colour.YELLOW + text + colour.END))
    elif spec.upper() == 'RED':
        print((colour.RED + text + colour.END))
    elif spec.upper() == 'PURPLE':
        print((colour.PURPLE + text + colour.END))
    elif spec.upper() == 'CYAN':
        print((colour.CYAN + text + colour.END))
    elif spec.upper() == 'DARKCYAN':
        print((colour.DARKCYAN + text + colour.END))
    elif spec.upper() == 'BLUE':
        print((colour.BLUE + text + colour.END))
    elif spec.upper() == 'UNDERLINE':
        print((colour.UNDERLINE + text + colour.END))


channelDictionary = {
    '01': 'ESPNNews',
    '02': 'ESPN',
    '03': 'ESPN 2',
    '04': 'ESPN U',
    '05': 'Fox Sports 1',
    '06': 'Fox Sports 2',
    '07': 'NFL Network',
    '08': 'NBA TV',
    '09': 'MLB Network',
    '10': 'NHL Network',
    '11': 'NBC Sports Network',
    '12': 'Golf Channel',
    '13': 'Tennis Channel',
    '14': 'CBS Sports Network',
    '15': 'Fight Network',
    '16': 'WWE Network',
    '17': 'Sportsnet World',
    '18': 'Sportsnet 360',
    '19': 'Sportsnet Ontario',
    '20': 'Sportsnet One',
    '21': 'TSN 1',
    '22': 'Univision Deportes',
    '23': 'ESPN Deportes',
    '24': 'Comedy Central',
    '25': 'Spike',
    '26': 'USA Network',
    '27': 'A&E',
    '28': 'TBS',
    '29': 'TNT',
    '30': 'SyFy',
    '31': 'Cartoon Network East',
    '32': 'HGTV',
    '33': 'CNN',
    '34': 'NBC East',
    '35': 'CBS East',
    '36': 'ABC East',
    '37': 'Fox East',
    '38': 'Viceland',
    '39': 'CNBC',
    '40': 'Fox News 360',
    '41': 'History Channel',
    '42': 'Discovery Channel',
    '43': 'National Geographic',
    '44': 'FX',
    '45': 'FXX',
    '46': 'BeIN USA',
    '47': 'AMC',
    '48': 'HBO East',
    '49': 'HBO Comedy',
    '50': 'HBO Signature',
    '51': 'HBO Zone',
    '52': 'Showtime East',
    '53': 'ActionMax HD East',
    '54': 'Cinemax Moremax',
    '55': 'Starz Cinema',
    '56': 'Starz East',
    '57': 'Starz Cinema',
    '58': 'Investigation America',
    '59': 'Cinemax East',
    '60': 'Cinemax 5 Star',
    '61': 'BBC America',
    '62': 'Fox Business',
    '63': 'Food Network',
    '64': 'E!',
    '65': 'MSNBC',
    '66': 'SCI',
    '67': 'Food Network',
    '68': 'Animal Planet',
    '69': 'Velocity',
    '70': 'US West',
    '71': 'US West',
    '72': 'US West',
    '73': 'Spectrum Sportsnet',
    '74': 'MMA Slot 1',
    '75': 'MMA Slot 2',
    '76': 'ePix',
    '77': 'ePix2',
    '78': 'ePix3',
    '79': 'TLC',
    '80': 'Lifetime',
    '81': 'Bravo',
    '82': 'DIY Network',
    '83': 'Oxygen',
    '84': 'CBC',
    '85': 'National Geographic Wild',
    '86': 'Univision',
    '87': 'Telemundo',
    '88': 'European Slot',
    '89': 'European Slot',
    '90': 'European Slot',
    '91': 'European Slot',
    '92': 'European Slot',
    '93': 'European Slot',
    '94': 'European Slot',
    '95': 'European Slot',
    '96': 'European Slot',
    '97': 'European Slot',
    '98': 'European Slot',
    '99': 'European Slot',
    '100': 'Willow',
    '101': 'Nick Jr',
    '102': 'Disney Channel',
    '103': 'Channel 103',
    '104': 'Channel 104',
    '105': 'EuroSport International 1',
    '106': 'EuroSport International 2',
    '107': 'Eir Sport 2',
    '108': 'BT Sport 1',
    '109': 'BT Sport 2',
    '110': 'BT Sport 3',
    '111': 'BT Sport ESPN',
    '112': 'Sky Sports News HQ',
    '113': 'Sky Sports Main',
    '114': 'Sky Sports Cricket',
    '115': 'Sky Sports Action',
    '116': 'Sky Sports Golf',
    '117': 'Sky Sports PL',
    '118': 'Sky Sports F1',
    '119': 'Sky Sports Mix',
    '120': 'Sky Sports Football',
    '121': 'Sky Sports Arena',
    '122': 'Racing UK',
    '123': 'Channel 123',
    '124': 'Channel 124',
    '125': 'Channel 125',
    '126': 'Channel 126',
    '127': 'Channel 127',
    '128': 'Channel 128',
    '129': 'Channel 129',
    '130': 'Channel 130',
    '131': 'Channel 131',
    '132': 'Channel 132',
    '133': 'Channel 133',
    '134': 'Channel 134',
    '135': 'Channel 135',
    '136': 'Channel 136',
    '137': 'Channel 137',
    '138': 'Channel 138',
    '139': 'Channel 139',
    '140': 'Channel 140',
    '141': 'Channel 141',
    '142': 'Channel 142',
    '143': 'Channel 143',
    '144': 'Channel 144',
    '145': 'Channel 145',
    '146': 'Channel 146',
    '147': 'Channel 147',
    '148': 'Channel 148',
    '149': 'Channel 149',
    '150': 'Channel 150'
}


if __name__ == '__main__':
    main()
