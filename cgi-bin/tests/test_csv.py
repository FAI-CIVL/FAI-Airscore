import csv, sys

def read_csv(csv_file):
    results = []
    with open(csv_file, mode='r') as f:
        reader = dict()
        try:
            reader = csv.DictReader(f, delimiter=';')
        except:
            print("Error: File {} is not a csv file".format(csv_file))
            sys.exit()
        for row in reader:
            result = {}
            for field in row:
                if row[field]:
                    result[field] = row[field]
            results.append(result)
        return results

def process_results(list):
    reader = []
    for row in list:
        r = dict()
        results = dict()
        for field in row:
            if field == 'Pilot' or field == 'id':
                r[field] = row[field]
            elif field:
                results[field] = row[field]
        r['results'] = results
        reader.append(r)
    return reader

def main():
    """Main module"""
    parsed_list = []
    results  = []
    """check parameter is good."""
    if len(sys.argv) > 1:
        """Get tasPk"""  
        filename = sys.argv[1]
        if len(sys.argv) > 2:
            """Test Mode""" 
            print('Running in TEST MODE')
            test = 1

        parsed_list = read_csv(filename)
        results = process_results(parsed_list)
        if test:
            for row in parsed_list:
                print (row)
            for row in results:
                print (row)

    else:
        print ("No file name. Use: python test_csv.py <filename>")

if __name__ == "__main__":
    main()
