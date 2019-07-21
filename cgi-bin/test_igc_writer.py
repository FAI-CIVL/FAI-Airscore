import sys, datetime, os, aerofiles
#from aerofiles.igc.reader import Reader

def main():
    """Main module"""
    test = 0
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""  
        track = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1

        with open(track, 'wb') as fp:
            writer = aerofiles.igc.Writer(fp)
            writer.write_headers({
                                    'manufacturer_code': 'XCS',
                                    'logger_id': 'TBX',
                                    'date': datetime.date(1987, 2, 24),
                                    'fix_accuracy': 50,
                                    'pilot': 'Tobias Bieniek',
                                    'copilot': 'John Doe',
                                    'glider_type': 'Duo Discus',
                                    'glider_id': 'D-KKHH',
                                    'firmware_version': '2.2',
                                    'hardware_version': '2',
                                    'logger_type': 'LXNAVIGATION,LX8000F',
                                    'gps_receiver': 'uBLOX LEA-4S-2,16,max9000m',
                                    'pressure_sensor': 'INTERSEMA,MS5534A,max10000m',
                                    'competition_id': '2H',
                                    'competition_class': 'Doubleseater',
                                })
        print(writer)

if __name__ == "__main__":
    main()
