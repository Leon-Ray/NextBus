# --------------------
# Name: Get_NextBus.py
# Purpose: Archive real time NextBus GPS data for the specified agency, route, and duration.
# Last Modified: 4/1/2013
# Author: Leon Raykin
# Python Version: 2.7
# --------------------

import urllib
import time
from xml.etree.ElementTree import parse
import csv
import os

#List of agencies
uagencies = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=agencyList')
agencies = {}
dict_count = 1
list = parse(uagencies)
for agency in list.findall('agency'):
	agencies[dict_count]=(agency.get('tag'))
	dict_count += 1

for key in agencies:
    print str(key) + ' ' + agencies[key]

agency_entry = agencies[input("Please select an agency from the above list (type the number only): ")]

#List of routes
uroutes = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=routeList&a=%s' % agency_entry)
routes = []
list = parse(uroutes)
for route in list.findall('route'):
	routes.append(route.get('tag'))

for i in routes:
        print i

route_entry = raw_input("Please select a route from the above list: ")

#Duration of data collection
duration_entry = raw_input("How long would you like to collect data for? Begin by specifying 'minutes', 'hours', or 'days' ")
if duration_entry == 'minutes':
        multiplier = 1
elif duration_entry == 'hours':
        multiplier = 60
elif duration_entry == 'days':
        multiplier = 1440

time_entry = raw_input('How many ' + duration_entry + ' of data would you like to collect? Decimals are OK. ')
length = float(time_entry)*multiplier*60

#Writes location data to CSV file
directory_entry = raw_input("Please specify the directory where you wish to save the file (e.g. C:\Users\Lraykin\Desktop\): ")
if not directory_entry[-1] == '\\':
        directory_entry = directory_entry + '\\'

if not os.path.exists (r'%s%s%s.csv' % (directory_entry, agency_entry, route_entry)):
        c = open(r'%s%s%s.csv' % (directory_entry, agency_entry, route_entry), 'wb')
else:
        x = 1
        for i in range(10):
                if os.path.exists (r'%s%s%s_%s.csv' % (directory_entry, agency_entry, route_entry, x)):
                        x += 1
                else:
                        c = open(r'%s%s%s_%s.csv' % (directory_entry, agency_entry, route_entry, x), 'wb')
                        break

writer = csv.writer(c)
writer.writerow(['Route', 'Bus_ID', 'Latitude', 'Longitude', 'Direction', 'Heading', 'Speed_kmh', 'Epoch_Time', 'Date', 'Time'])

start_time = time.time()
dup = []

attempt = 1
def repeat():      
        ulocation = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=%s&r=%s&t=0' % (agency_entry, route_entry))
        list = parse(ulocation)

        global dup
        for raw in list.findall('vehicle'):
                duplicates = 0
                for i in dup:
                        if (raw.get('lat') == i[0] and raw.get('lon') == i[1]):
                                duplicates += 1
                if duplicates < 1:
                        epoch_time = time.time()-int(raw.get('secsSinceReport'))
                        report_date = time.strftime('%x', time.localtime(epoch_time))
                        report_time = time.strftime('%X', time.localtime(epoch_time))
                        writer.writerow([raw.get('routeTag'), raw.get('id'), raw.get('lat'), raw.get('lon'), raw.get('dirTag'), raw.get('heading'), raw.get('speedKmHr'), epoch_time, report_date, report_time])
        
        dup = []
        for raw in list.findall('vehicle'):
                temp = []
                lat = str(raw.get('lat'))
                temp.append(lat)
                lon = str(raw.get('lon'))
                temp.append(lon)
                dup.append(temp)
        return dup
                
#Writes backup XML files
counter = 1

if not os.path.exists(r'%sbackup' % directory_entry):
        os.makedirs(r'%sbackup' % directory_entry)
        
def backup():
        global counter
        ulocation = urllib.urlopen('http://webservices.nextbus.com/service/publicXMLFeed?command=vehicleLocations&a=%s&r=%s&t=0' % (agency_entry, route_entry))
        data = ulocation.read()
        f = open (r'%s\backup\%s%s_%s.xml' % (directory_entry, agency_entry, route_entry, counter), 'wb')
        f.write(data)
        f.close()
        counter += 1
        return counter


#Pings the XML feed and collects data for the specified duration
while (time.time() < start_time+float(length)):
        try:
                repeat()
                backup()
                time.sleep(30)
        except:
                if attempt < 11:
                        print 'An error occurred.  Retry attempt ' + str(attempt) + ' of 10.'
                        time.sleep(60)
                        repeat()
                        backup()
                        attempt += 1
                else:
                        print 'An error occured.  Download could not be completed.'
                        c.close()
                
c.close()

print 'Data Collection Complete!'
