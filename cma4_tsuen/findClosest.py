import urllib.request
import json
import dml
import prov.model
import datetime
import uuid
from math import sin, cos, sqrt, atan2, radians
import sys

class findClosest(dml.Algorithm):
    contributor = 'cma4_tsuen'
    reads = ['cma4_tsuen.destinationsProjected', 'cma4_tsuen.stationsProjected']
    writes = ['cma4_tsuen.closest']

    def latLongDist(p, q):
        p = (radians(p[0]), radians(p[1]))
        q = (radians(q[0]), radians(q[1]))
        dlon = q[1] - p[1]
        dlat = q[0] - p[0]

        a = sin(dlat / 2)**2 + cos(lat1) * cos(lat2) * sin(dlon / 2)**2
        c = 2 * atan2(sqrt(a), sqrt(1 - a))
        return 6373 * c

    @staticmethod
    def execute(trial = False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_tsuen', 'cma4_tsuen')

        destinations = repo['cma4_tsuen.destinationsProjected'].find()
        stations = repo['cma4_tsuen.stationsProjected'].find()

        final = []

        # finds closest station to each destination
        for d in destinations:
            destCoords = d['coords']
            closestStation = None
            minDist = sys.maxsize
            minStationCoords = (0, 0)
            for s in stations:
                scoords = s['coords']
                dist = findClosest.latLongDist(destCoords, scoords)
                if dist < minDist:
                    closestStation = s['key']
                    minDist = dist
                    minStationCoords = scoords
            d['closestStation'] = closestStation
            d['stationCoords'] = minStationCoords
            final.append(d)

        repo.dropCollection("cma4_tsuen.closest")
        repo.createCollection("cma4_tsuen.closest")
        repo['cma4_tsuen.closest'].insert_many(final)
        repo['cma4_tsuen.closest'].metadata({'complete':True})
        print(repo['cma4_tsuen.closest'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start":startTime, "end":endTime}
    
    @staticmethod
    def provenance(doc = prov.model.ProvDocument(), startTime = None, endTime = None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('cma4_tsuen', 'cma4_tsuen')
        doc.add_namespace('alg', 'http://datamechanics.io/algorithm/') # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat', 'http://datamechanics.io/data/') # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont', 'http://datamechanics.io/ontology#') # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/') # The event log.
        doc.add_namespace('destinations', 'http://datamechanics.io/')
        doc.add_namespace('stations', 'http://datamechanics.io/')

        this_script = doc.agent('alg:cma4_tsuen#closest', {prov.model.PROV_TYPE:prov.model.PROV['SoftwareAgent'], 'ont:Extension':'py'})
        resource = doc.entity('dat:destinationsProjected', {'prov:label':'Destinations Name and Coords', prov.model.PROV_TYPE:'ont:DataResource', 'ont:Extension':'json'})
        resource2 = doc.entity('dat:stationsProjected', {'prov:label':'Stations stationsProjected Name and Data', prov.model.PROV_TYPE:'ont:DataSet', 'ont:Extension':'json'})
        get_closest = doc.activity('log:uuid'+str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_closest, this_script)
        doc.usage(get_closest, resource, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Retrieval'
                  }
                  )
        doc.usage(get_closest, resource2, startTime, None,
                  {prov.model.PROV_TYPE:'ont:Computation'
                  }
                  )

        destinationsProjected = doc.entity('dat:cma4_tsuen#destinationsProjected', {prov.model.PROV_LABEL:'Projected Destinations', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(destinationsProjected, this_script)
        doc.wasGeneratedBy(destinationsProjected, get_closest, endTime)
        doc.wasDerivedFrom(destinationsProjected, resource, get_closest, get_closest, get_closest)

        stationsProjected = doc.entity('dat:cma4_tsuen#stationsProjected', {prov.model.PROV_LABEL:'Projected Stations', prov.model.PROV_TYPE:'ont:DataSet'})
        doc.wasAttributedTo(stationsProjected, this_script)
        doc.wasGeneratedBy(stationsProjected, get_closest, endTime)
        doc.wasDerivedFrom(stationsProjected, resource, get_closest, get_closest, get_closest)

        repo.logout()
                  
        return doc

findClosest.execute()
doc = findClosest.provenance()
print(doc.get_provn())
print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof