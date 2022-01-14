''' Bird traffic simulation plugin '''
from re import I
from wsgiref.handlers import IISCGIHandler
import numpy as np

import bluesky as bs
from bluesky import stack
from bluesky.tools.aero import ft, kts
from bluesky.stack.cmdparser import append_commands
from bluesky.core.walltime import Timer

def init_plugin():

    config = {
        # The name of your plugin
        'plugin_name'      : 'BIRDSIM',
        'plugin_type'      : 'sim',
        'update'           : update,
        'reset'            : reset
        }

    return config

def update():
    # do modelling here. update bird state lat,lon,alt,hdg,etc

    ...

def reset():
    # clear everything. TODO: smarter way to do this
    bird_traf.reset()
    
    # release birds with no info to clear screen TODO: smarter way to do this
    bird_traf.release_birds()

@stack.command(name='CREBIRD')
def CREBIRD(birdid, birdtype: str="goose", birdlat: float=52., birdlon: float=4., birdhdg: float=None, birdalt: float=0,  
        birdspd: float = 0):
    ''' CREBIRD birdid,type,lat,lon,hdg,alt,spd '''
    # correct some argument units
    birdspd *= kts
    birdalt *= ft

    # create the bird
    bird_traf.create(birdid, birdtype, birdlat, birdlon, birdhdg, birdalt, birdspd)



@stack.command(name = 'DELBIRD')
def DELBIRD(birdid):
    # bird left the area, landed or was eaten by an aircraft
    bird_traf.remove_bird(birdid)


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


        '''        # to make testing a bit easier: add syntax for CREBIRD to the gui
        cmd_dict = {        
            "CREBIRD": [
            "CREBIRD birdid,birdtype,lat,lon,hdg,alt,spd",
            "txt,txt,latlon,[hdg,alt,spd]",
            self.create,
            "Create a birdie",
        ],}

        append_commands(cmd_dict)
        
        
        --> probably already in the@stackcommand / the definition of the function. Seems only to work
        for non-plugin functions (e.g addwptmode yes (in route) but metrics (plugin metrics))
        
        '''

        # Update rate of aircraft update messages [Hz]
        birdupdate_rate = 5

        # create a timer to send bird data
        self.fast_timer = Timer()
        self.fast_timer.timeout.connect(self.release_birds)
        self.fast_timer.start(int(1000 / 5))

        # add or change any arrays you like
    
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
        '''release them to the visual world '''
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
        
        return
 
    def remove_bird(self, birdid):
        print ("we attempt to delete birdie ", birdid)
        
        index_to_remove = self.id2idx(birdid)
        
        
        self.nbird = self.nbird - 1 # number of birds
        
        # basic info

        del self.id [index_to_remove]   # identifier (string)
        del self.type[index_to_remove]   # bird type (string)

        # Positions
        self.lat              = np.delete(self.lat, index_to_remove)
        self.lon              = np.delete(self.lon, index_to_remove)  
        self.alt              = np.delete(self.alt, index_to_remove)       
        self.hdg              = np.delete(self.hdg, index_to_remove)  
        

        # Velocities
        self.hs     = np.delete(self.hs, index_to_remove)    # horizontal airspeed [m/s]
        self.vs     = np.delete(self.vs, index_to_remove)   # vertical speed [m/s]
        
        
        
        '''from here on, it is copied from birds.py '''
        # as soon as a bird leaves the simulation, its information has to be removed
        # idx is the index, where the bird info is stored per list
        
        # also gets called when a bird gets hit by an aircraft

        # mark the bird as removed
        '''self.removed_id = np.append(self.removed_id, self.id[index_to_remove])
        
        self.last_ts          = np.delete(self.last_ts, index_to_remove)
        self.last_lat         = np.delete(self.last_lat, index_to_remove)
        self.last_lon         = np.delete(self.last_lon, index_to_remove)
        
        self.next_ts          = np.delete(self.next_ts, index_to_remove)
        self.next_lat         = np.delete(self.next_lat, index_to_remove)
        self.next_lon         = np.delete(self.next_lon, index_to_remove)        
        
        
        
        self.lat              = np.delete(self.lat, index_to_remove)
        self.lon              = np.delete(self.lon, index_to_remove)
        self.trk              = np.delete(self.trk, index_to_remove)    
        self.alt              = np.delete(self.alt, index_to_remove)
        self.tas              = np.delete(self.tas, index_to_remove)
        self.id               = np.delete(self.id, index_to_remove)   
        self.bird_size        = np.delete(self.bird_size, index_to_remove)
        self.no_inds          = np.delete(self.no_inds, index_to_remove)
        self.flock_flag       = np.delete(self.flock_flag, index_to_remove)
        self.collision_radius = np.delete(self.collision_radius, index_to_remove)'''
        
        '''and here also some logging'''





        return    
    
    
    
    def reset(self):
        # clear all TODO: copy traffarrays
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
        
        return


# initialize bird traffic
bird_traf = BirdTraffic()

