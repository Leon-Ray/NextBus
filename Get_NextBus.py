# --------------------
# Name: Get_NextBus.py
# Purpose: Archive real time NextBus GPS data for the specified agency, route, and duration.
# Author: Leon Raykin
# Python Version: 2.7
# --------------------

import csv
import os
import urllib
from xml.etree.ElementTree import parse
from datetime import datetime
import time

basepath = 'C:/Users/lraykin.ITERIS/Desktop/Nextbus/'
refresh_rate = 15 #number of seconds between refreshing the data feed

def main():
    duration_secs = set_duration()
    nb = NextBus()
    agency = nb.set_agency()
    route = nb.set_route(agency)
    start_time = time.time()
    while (time.time() < start_time+duration_secs): 
        nb.get_data(agency, route)
        nb.remove_duplicates(refresh_rate)
        nb.add_timestamp()
        nb.export_csv(basepath)
        nb.download_xml(basepath)
        time.sleep(refresh_rate)
    print 'Data collection completed at ' + datetime.now().strftime('%Y-%m-%d %H:%M:%S') + '.'

def set_duration():
    duration_type = raw_input('How long would you like to collect data for? Begin by specifying "minutes", "hours", or "days": ')
    def to_secs(duration_type):
        if duration_type == 'minutes':
            return 60
        if duration_type == 'hours':
            return 3600
        if duration_type == 'days':
            return 86400
    duration = raw_input('How many ' + duration_type + ' of data would you like to collect? ')
    seconds = float(duration)*to_secs(duration_type)
    return seconds

class NextBus():
    def __init__(self):
        self.count = 0
    def set_agency(self):
        uagencies = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList')
        agencies = parse(uagencies)
        agency_dict = {}
        count = 1
        for agency in agencies.findall('agency'):
            agency_dict[count]=(agency.get('tag'))
            count += 1
        for key, value in agency_dict.iteritems():
            print str(key) + ' ' + value
        self.agency = agency_dict[input('Enter the desired agency number shown above: ')]
        return self.agency
    def set_route(self, agency=None):
        if agency:
            self.agency = agency
        uroutes = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=routeList&a=' + self.agency)
        routes = parse(uroutes)
        route_list = []
        for route in routes.findall('route'):
            route_list.append(route.get('tag'))
        for route in route_list:
            print route
        self.route = raw_input('Select a route from the above list: ')   
        return self.route
    def get_data(self, agency=None, route=None):
        if agency:
            self.agency = agency
        if route:
            self.route = route
        self.data = []
        self.headers = ['id', 'routeTag', 'dirTag', 'lat', 'lon', 'secsSinceReport', 'predictable', 'heading', 'speedKmHr']
        self.dl_time = time.time()
        ulocation = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=%s&r=%s&t=0' % (self.agency, self.route))
        xml_data = parse(ulocation)
        for raw in xml_data.findall('vehicle'):
            record = {}
            for field in self.headers:
                record[field] = raw.get(field)
            self.data.append(record)
        self.count += 1
        print 'Download Count: ' + str(self.count) + '\t Agency: ' + self.agency + '\t Route: ' + self.route + '\t Number of Records: ' + str(len(self.data)) + '\t Time: ' +  datetime.now().strftime('%Y-%m-%d %H:%M:%S')
        return self.data
    def remove_duplicates(self, refresh_rate):
        before_len = len(self.data)
        if self.count > 1:
            self.data = [record for record in self.data if int(record['secsSinceReport']) < refresh_rate] 
        after_len = len(self.data)
        print 'Removed ' + str(before_len-after_len) + ' duplicates.'
    def add_timestamp(self):
        for record in self.data:
             bus_time = self.dl_time - int(record['secsSinceReport'])
             record['UTC_timestamp'] = time.strftime('%m/%d/%Y %H:%M:%S',  time.gmtime(bus_time))
        self.headers.append('UTC_timestamp')
        print 'Added UTC timestamp to data.'
    def export_csv(self, basepath, agency=None, route=None):
        if agency:
            self.agency = agency
        if route:
            self.route = route
        outfileName = open(basepath + self.agency + self.route + '.csv', 'ab')
        outfile = csv.writer(outfileName)  
        if self.count == 1:
            outfile.writerow(self.headers)
        for record in self.data:
            data = []
            for column in self.headers:
                data.append(record[column])
            outfile.writerow(data)
        outfileName.close()
        print "Added " + str(len(self.data)) + " records to csv file."
    def download_xml(self, basepath, agency=None, route=None): #secsSinceReport will not match data in csv file
        if not os.path.exists(basepath + 'backup'):
            os.makedirs(basepath + 'backup')
        ulocation = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=%s&r=%s&t=0' % (self.agency, self.route))
        xml_data = ulocation.read()
        f = open(basepath + 'backup/' + self.agency + self.route + '_' + str(self.count) + '.xml', 'wb')
        f.write(xml_data)
        f.close()
        print 'Downloaded one backup xml file. \n'

if __name__ == '__main__':
    main()