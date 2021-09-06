''' Bird traffic simulation plugin '''
import numpy as np

import bluesky as bs
from bluesky import stack
from bluesky.tools.aero import ft, kts


def init_plugin():

    config = {
        # The name of your plugin
        'plugin_name'      : 'BIRDSIM',
        'plugin_type'      : 'sim',
        'update'           : update
        }

    return config

def update():

    # do modelling here. update bird state lat,lon,alt,hdg,etc
    
    # send data to bird gui (this should be last step of your things)
    bird_traf.release_birds()

@stack.command
def CREBIRD(birdid, birdtype: str="goose", birdlat: float=52., birdlon: float=4., birdhdg: float=None, birdalt: float=0,  
        birdspd: float = 0):
    ''' CREBIRD birdid,type,lat,lon,hdg,alt,spd '''
    # correct some argument units
    birdspd *= kts
    birdalt *= ft

    # create the bird
    bird_traf.create(birdid, birdtype, birdlat, birdlon, birdhdg, birdalt, birdspd)


class BirdTraffic():
    # TODO: need to figure out how to delete things in a smart way
    def __init__(self):

        self.nbird = 0 # number of birds
        
        # initialize bid array
        self.id      = []  # identifier (string)
        self.type    = []  # bird type (string)

        # Positions
        self.lat     = np.array([], dtype=float)  # latitude [deg]
        self.lon     = np.array([], dtype=float)  # longitude [deg]
        self.alt     = np.array([], dtype=float)  # altitude [m]
        self.hdg     = np.array([], dtype=float)  # traffic heading [deg]

        # Velocities
        self.hs     = np.array([], dtype=float)   # horizontal airspeed [m/s]
        self.vs     = np.array([], dtype=float)  # vertical speed [m/s]

        # add or change anny arrays you like
    
    def create(self, birdid, birdtype="goose", birdlat=52., birdlon=4., birdhdg=None, birdalt=0, birdspd=0):
        # add one bird
        n = 1

        # increase number of birds
        self.nbird += n

        # get position of bird
        birdlat = np.array(n * [birdlat])
        birdlon = np.array(n * [birdlon])

        # Limit longitude to [-180.0, 180.0]
        birdlon[birdlon > 180.0] -= 360.0
        birdlon[birdlon < -180.0] += 360.0

        # add to birdinfo to lists
        self.id.append(birdid)
        self.type.append(birdtype)

        # Positions
        self.lat = np.append(self.lat, birdlat)
        self.lon = np.append(self.lon, birdlon)
        self.alt = np.append(self.alt, birdalt)

        # Heading
        self.hdg = np.append(self.hdg, birdhdg)

        # Velocities
        self.hs = np.append(self.hs, birdspd)
        vs = 0
        self.vs = np.append(self.vs, vs)

    def id2idx(self, birdid):
        """Find index of bird id"""
        return self.id.index(birdid.upper())
    
    def release_birds(self):
        data = dict()
        data['id']         = self.id
        data['type']       = self.type
        data['lat']        = self.lat
        data['lon']        = self.lon
        data['alt']        = self.alt
        data['hdg']        = self.hdg
        data['vs']         = self.vs
        data['hs']         = self.hs

        # send bird data
        bs.net.send_stream(b'BIRDDATA', data)


# initialize bird traffic
bird_traf = BirdTraffic()

