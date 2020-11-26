# -*- coding: utf-8 -*-
"""
CIVLRankings Library
contains all functions to get informations from CIVL database

Use: import civlrankings

Antonio Golfari - 2019
"""

import xml.etree.ElementTree as ET

import requests

url = "http://civlrankings.fai.org/FL.asmx"
headers = {'content-type': 'text/xml'}


def create_participant_from_CIVLID(civl_id):
    """get pilot info from CIVL database and create Participant obj"""
    from pilot.participant import Participant

    body = f"""<?xml version='1.0' encoding='utf-8'?>
                <soap12:Envelope xmlns:xsi='http://www.w3.org/2001/XMLSchema-instance' xmlns:xsd='http://www.w3.org/2001/XMLSchema' xmlns:soap12='http://www.w3.org/2003/05/soap-envelope'>
                    <soap12:Body>
                        <GetPilot xmlns='http://civlrankings.fai.org/'>
                            <CIVLID>{civl_id}</CIVLID>
                        </GetPilot>
                    </soap12:Body>
                </soap12:Envelope>"""
    response = requests.post(url, data=body, headers=headers)
    # print(response.content)
    root = ET.fromstring(response.content)
    data = root.find('.//{http://civlrankings.fai.org/}GetPilotResponse')
    if not data or not data.find('{http://civlrankings.fai.org/}GetPilotResult'):
        '''we don't have a result'''
        return None
    result = data.findall('{http://civlrankings.fai.org/}GetPilotResult//')
    pilot = Participant(civl_id=civl_id)
    pilot.name = result[0].text
    pilot.nat = result[1].text
    pilot.sex = 'F' if result[6].text == 'true' else 'M'
    pilot.team = result[7].text
    pilot.glider = result[8].text
    return pilot


def create_participant_from_name(name):
    """get pilot info from pilot name database and create Participant obj
    It's almost sure that we get more than one result.
    This function gives back a Participant ONLY if we get a single result.
    get_pilots_from_name gives a list of Dict"""
    from pilot.participant import Participant

    body = f"""<?xml version="1.0" encoding="utf-8"?>
                <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                  <soap12:Body>
                    <FindPilot xmlns="http://civlrankings.fai.org/">
                      <name>{name}</name>
                    </FindPilot>
                  </soap12:Body>
                </soap12:Envelope>"""
    response = requests.post(url, data=body, headers=headers)
    # print(response.content)
    root = ET.fromstring(response.content)
    data = root.find('.//{http://civlrankings.fai.org/}FindPilotResponse')
    if not len(data.findall('{http://civlrankings.fai.org/}FindPilotResult/')) == 1:
        '''we don't have a single result'''
        return None

    result = data.findall('{http://civlrankings.fai.org/}FindPilotResult//')
    pilot = Participant()
    pilot.name = result[1].text
    pilot.nat = result[2].text
    pilot.civl_id = int(result[6].text)
    pilot.sex = 'F' if result[7].text == 'true' else 'M'
    pilot.team = result[8].text
    pilot.glider = result[9].text
    return pilot


def get_pilots_from_name(name):
    """get a list of Dict, for pilots in CIVL database with similar name"""

    body = f"""<?xml version="1.0" encoding="utf-8"?>
                <soap12:Envelope xmlns:xsi="http://www.w3.org/2001/XMLSchema-instance" xmlns:xsd="http://www.w3.org/2001/XMLSchema" xmlns:soap12="http://www.w3.org/2003/05/soap-envelope">
                  <soap12:Body>
                    <FindPilot xmlns="http://civlrankings.fai.org/">
                      <name>{name}</name>
                    </FindPilot>
                  </soap12:Body>
                </soap12:Envelope>"""
    response = requests.post(url, data=body, headers=headers)
    # print(response.content)
    root = ET.fromstring(response.content)
    data = root.find('.//{http://civlrankings.fai.org/}FindPilotResponse')
    if len(data.findall('{http://civlrankings.fai.org/}FindPilotResult/')) == 0:
        '''we don't have a single result'''
        return None

    results = data.findall('.//{http://civlrankings.fai.org/}Person')
    pilots = []
    for p in results:
        pil = {
            'name': p[0].text,
            'civl_id': int(p[5].text),
            'nat': p[1].text,
            'sex': 'F' if p[6].text == 'true' else 'M',
        }
        pilots.append(pil)
    return pilots
