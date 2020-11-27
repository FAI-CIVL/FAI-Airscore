"""
KML track files reader
Use:    import kml
        with open(track, 'r', encoding='utf-8') as f:
                result = kml.Reader().read(f)

Antonio Golfari - 2018
"""

import datetime

import lxml.etree as ET


class Reader:
    """
    A reader for the KML flight log file format.
    """

    def __init__(self):
        self.reader = None

    def read(self, fp):
        message = ''
        """read the xml file"""
        tree = ET.parse(fp)
        root = tree.getroot()
        # print("Root: {} \n".format(root.tag))

        """Define result dict() parts"""
        logger_id = [[], None]
        fix_records = [[], []]
        task = [[], {"waypoints": []}]
        dgps_records = [[], []]
        event_records = [[], []]
        satellite_records = [[], []]
        security_records = [[], []]
        header = [[], {}]
        fix_record_extensions = [[], []]
        k_record_extensions = [[], []]
        k_records = [[], []]
        comment_records = [[], []]

        """get track infos"""
        for el in root.iter('Metadata'):
            if el.get('type') == 'track':
                message += f"TYPE: {el.get('type')} \n"
                """get track source"""
                source = "{} ver. {}".format(el.get('src'), el.get('v'))
                message += f"Source: {source} \n"
                """get first point time"""
                start = el.find('FsInfo').get('time_of_first_point')
                message += f"Start: {start} \n"
                """get instrument if available"""
                try:
                    instrument = el.find('FsInfo').get('instrument')
                except:
                    instrument = ''
                message += f"Instrument: {instrument} \n"
                """get time from first point"""
                timelist = el.find('FsInfo').find('SecondsFromTimeOfFirstPoint').text.split()
                """get pressure altitude and security hash

                    in old GPS Dump versions, it seems that both could miss
                    maybe we have to get a notice when they miss?
                """
                try:
                    preslist = el.find('FsInfo').find('PressureAltitude').text.split()
                except:
                    preslist = [0] * len(timelist)
                try:
                    hash = el.find('FsInfo').get('hash')
                    message += f"Hash: {hash} \n"
                except:
                    hash = None

                """get coordinates"""
                coordlist = el.getparent().find('LineString').find('coordinates').text.split()

        """create datetime obj from string"""
        flightdate = datetime.datetime.strptime(start, "%Y-%m-%dT%H:%M:%S")
        time = flightdate.time()
        day = flightdate.date()

        """create dict() of logger id"""
        logger_id[1] = self.decode_A_record(source)
        """create dict() of header"""
        header[1].update(self.decode_H_record(instrument, day))
        """add Hash if present"""
        security_records[1].append(hash)

        """create a fix list"""
        pointlist = []
        for i in range(len(timelist)):
            """calculate point time"""
            d = int(timelist[i])
            gpstime = (flightdate + datetime.timedelta(seconds=d)).time()
            """split coord in lat, lon, gpsalt"""
            var = []
            try:
                var = coordlist[i].split(',')
            except:
                """manage rare case of empty coords"""
                var = [None, None, None]
            pointlist.append([i, gpstime, preslist[i], var[0], var[1], var[2]])
            """create list of fix"""
            fix_records[1].append(self.decode_B_record(pointlist[i]))

        """returns the result dict()"""
        return dict(
            logger_id=logger_id,  # A record
            fix_records=fix_records,  # B records
            task=task,  # C records
            dgps_records=dgps_records,  # D records
            event_records=event_records,  # E records
            satellite_records=satellite_records,  # F records
            security_records=security_records,  # G records
            header=header,  # H records
            fix_record_extensions=fix_record_extensions,  # I records
            k_record_extensions=k_record_extensions,  # J records
            k_records=k_records,  # K records
            comment_records=comment_records,  # L records
        )

    @staticmethod
    def decode_B_record(line):
        return {
            'time': line[1],
            'lat': float(line[4]),
            'lon': float(line[3]),
            'validity': 'A',
            'pressure_alt': int(line[2]),
            'gps_alt': int(line[5]),
        }

    @staticmethod
    def decode_A_record(src):
        return {'manufacturer': '', 'id': '', 'id_addition': src}

    @staticmethod
    def decode_H_record(instrument, date):
        if instrument is not '':
            manufacturer, model = instrument.split(' ', 1)
            value = {'logger_manufacturer': manufacturer, 'logger_model': model}
        value['utc_date'] = date
        return value
