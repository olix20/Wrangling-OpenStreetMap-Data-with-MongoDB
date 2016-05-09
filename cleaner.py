#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
Your task is to use the iterative parsing to process the map file and
find out not only what tags are there, but also how many, to get the
feeling on how much of which data you can expect to have in the map.
Fill out the count_tags function. It should return a dictionary with the 
tag name as the key and number of times this tag can be encountered in 
the map as value.

Note that your code will be tested with a different data file than the 'example.osm'
"""
import xml.etree.cElementTree as ET
import pprint
import re
from collections import defaultdict
from pymongo import MongoClient
import codecs
import json


OSMFILE = "smallSingapore.osm"
lower = re.compile(r'^([a-z]|_)*$')
lower_colon = re.compile(r'^([a-z]|_)*:([a-z]|_)*$')
problemchars = re.compile(r'[=\+/&<>;\'"\?%#$@\,\. \t\r\n]')
street_type_re = re.compile(r'\b\S+\.?$', re.IGNORECASE)
phone_re = re.compile(r'(60|65|\+60|\+65)?\D?(\d{4})\D?(\d{4})', re.IGNORECASE)
housenumber_re = re.compile(r'(\d+[a-z]?|#?\d{2}-\d{2}|blk \d+)', re.IGNORECASE)
source_re = re.compile(r'^(\w\s?)+$', re.IGNORECASE)
posstcode_re = re.compile(r'^\d{6}$')

CREATED = [ "version", "changeset", "timestamp", "user", "uid"]

expected = ["Street", "Avenue", "Boulevard", "Drive", "Court", "Place", "Square", "Lane", "Road", 
            "Trail", "Parkway", "Commons", "Way", "Walk", "View", "Valley", "Green", "Crescent", "Terrace", "road"]

# UPDATE THIS VARIABLE
mapping = { 
            "Ave": "Avenue",
            "Rd." : "Road",
            "Rd" : "Road",
            "Jl." : "Jalan ",
            "Jl" : "Jalan",
            "Jln" : "Jalan",
            "Btk" : "Butik",
            "Upp" : "Upper"
            }
			
			


def count_tags(filename):
        # YOUR CODE HERE
        tags = {}
        tree = ET.parse(filename)
        for line in tree.iter():
            #print line.tag
            if not tags.get(line.tag):
                tags[line.tag] = 1
            else:
                tags[line.tag] = tags[line.tag] + 1
            
        return tags


def key_type(element, keys):
    if element.tag == "tag":
        # YOUR CODE HERE
        if problemchars.search(element.attrib['k']):
            keys['problemchars'] +=1
            #print element.attrib['k']
        elif lower_colon.search(element.attrib['k']):
            keys['lower_colon'] +=1
        elif lower.search(element.attrib['k']):
            keys['lower'] +=1    
        else: 
            keys['other'] +=1
        
        
    return keys



def cleanName(name):
    #m = street_type_re.search(street_name)
    #jalan_re = re.compile(r'Jl\.')
    
    for key,val in mapping.iteritems():
        name = re.sub(key,val, name)
 
    return name
			

def cleanPhoneNumber(phone_number):
    
    #print phone_number
    if not phone_number:
	    return 	

    phone_number = phone_number.replace(" ", "")
    phone_number = phone_number.replace("-", "")
    if len(phone_number) == 8 :
        phone_number = "+65" + phone_number 

    m = phone_re.search(phone_number)
    if not m:
        print "EXCEPTION phone Number: " +phone_number    
        return None
    else:
        return m.group()	

def cleanHouseNumber(house_number):
    
    #print house
    if not house_number:
        return
    
    m = housenumber_re.search(house_number)
    if not m:
        print "EXCEPTION House Number: " +house_number
        return None
    else:
        #print m.group()			
        return m.group()



def cleanPostCode(postcode):
    
    #print house
    if not postcode:
        return None
    
    m = posstcode_re.search(postcode.strip())
    if not m:
        print "EXCEPTION postcode: " +postcode
        return None
    else:
        #print m.group()			
        return m.group()


	
	
def is_streetName_or_name(elem):
    return (elem.attrib['k'] == "addr:street" or elem.attrib['k'] == "name")
def is_phone_number(elem):
    return (elem.attrib['k'] == "phone")
def is_house_number(elem):
    return (elem.attrib['k'] == "addr:housenumber")	
def is_source(elem):
    return (elem.attrib['k'] == "source")	


def audit(osmfile):
    osm_file = open(osmfile, "r")
    street_types = defaultdict(set)
    for event, elem in ET.iterparse(osm_file, events=("start",)):

        if elem.tag == "node" or elem.tag == "way":
            '''
            for tag in elem.iter("tag"):
                if is_street_name(tag):
                    audit_street_type(street_types, tag.attrib['v'])
                elif is_phone_number(tag):
                    cleanPhoneNumber(tag.attrib['v'])
                elif is_house_number(tag):
                    cleanHouseNumber(tag.attrib['v'])                    
                if tag.attrib['k'] == "addr:postcode":
                   cleanPostCode(tag.attrib['v'])  
            '''
            shape_element(elem)        
    return street_types
	
					
					
def update_name(name, mapping):

    # YOUR CODE HERE
    for key, val in mapping.iteritems():
        #print key
        if name.find(key)>-1:
            name = name.replace(key,val)
            break
        #

    return name
	

def shape_element(element):
    node = {}
    if  element.tag == "node" or element.tag == "way" :
        # YOUR CODE HERE
        node['id'] =  element.get('id')
        node['type'] =  element.tag 
        node['visible'] =  "true"
        node['names']={}
        node['address'] = {}
        node['node_refs'] =[]
        node['created']={}
        
        
        for c in CREATED:
            node['created'][c] = element.get(c)
        
        if element.get('lat') and element.get('lon'):
            node['pos'] = [float(element.get('lat')),float(element.get('lon'))]
            
        for tag in element.iter('tag'):
            if not tag.get('k') or problemchars.search(tag.get('k')) :
                continue
                
            #we're not interested in nodes/edjes belonging to Malaysia or Indonesia    
            if not inSingapore(tag) :
                return None
                
            tagKey = tag.get('k')
            if tagKey.startswith(':'): 
                tagKey = tagKey[1:]
   
            if tagKey.startswith('name:'): #storing names in other languages: zh, ms, en, in
                node['names'][tagKey[5:]] = tag.get('v')			
            elif tagKey.startswith('alt_name:'):
                node['names']['alt'] = tag.get('v')			
            elif tagKey == 'name':
                node['name'] = cleanValue(tag)                
    
            elif tagKey.startswith('addr:'):
                node['address'][tagKey[5:]] = cleanValue(tag)	
            	                
            else:
                node[tagKey] = tag.get('v')	
                        
		
        for tag in element.iter('nd'):
            node['node_refs'].append(tag.get('ref'))
        
        #pprint.pprint(node)
        return node 
    else:
        return None
	

def cleanValue(tag):
    #print ":D"
     
    if is_streetName_or_name(tag):
        return cleanName(tag.attrib['v'])
    elif is_phone_number(tag):
        return cleanPhoneNumber(tag.attrib['v'])
    elif is_house_number(tag):
        return cleanHouseNumber(tag.attrib['v'])                    
    elif tag.attrib['k'] == "addr:postcode":
        return cleanPostCode(tag.attrib['v'])  
                   
	
def test():

    #tags = count_tags('sample.osm')
    #print "types of tags in the sample:"
    #pprint.pprint(tags)
	
    process_map('smallSingapore.osm')
    #pprint.pprint(keys)	
    #st_types = audit(OSMFILE)
	#pprint.pprint(dict(st_types))

    #audit_postalcodes(OSMFILE)
    #audit_phone(OSMFILE)
    #audit_houseNumber(OSMFILE)
    #audit_source(OSMFILE)

	
    #data = process_map(OSMFILE, True)
    
def process_map(file_in, pretty=False ):
    # You do not need to change this file
    file_out = "{0}.json".format(file_in)
    data = []
    client = MongoClient()
    db = client.cities
    collection = db.sg
    
    with codecs.open(file_out, "w") as fo:
        for _, element in ET.iterparse(file_in):
            
            el = shape_element(element)
            if el:
                data.append(el)
                
                
                
                if pretty:
                    fo.write(json.dumps(el, indent=2)+"\n")
                else:
                    fo.write(json.dumps(el) + "\n")
    
        
    
    collection.insert_many(data)    #write into mongodb    
    
    return data

def inSingapore(tag):
    
    if tag.get('k') == "addr:city" and tag.get('v') != 'Singapore':
        return False
    if tag.get('k') == "is_in:country" and tag.get('v') != 'Singapore'    :
        return False
    if tag.get('k') == "addr:country" and tag.get('v') != 'SG'    :
        return False
        

    return True
    
if __name__ == "__main__":
    test()