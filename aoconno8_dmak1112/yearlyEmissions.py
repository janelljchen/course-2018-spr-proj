import urllib.request
import json
import dml
import prov.model
import datetime
import uuid


class yearlyEmissions(dml.Algorithm):
    contributor = 'aoconno8_dmak1112'
    reads = []
    writes = ['aoconno8_dmak1112.yearlyEmissions']

    @staticmethod
    def execute(trial=False):
        '''Retrieve some data sets (not using the API here for the sake of simplicity).'''
        startTime = datetime.datetime.now()
        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('aoconno8_dmak1112', 'aoconno8_dmak1112')
        url = 'https://data.boston.gov/api/3/action/datastore_search?resource_id=bd8dd4bb-867e-4ca2-b6c7-6c3bd9e6c290&limit=176'
        response = urllib.request.urlopen(url).read().decode("utf-8")
        emissions_json = [json.loads(response)]
        repo.dropCollection("yearlyEmissions")
        repo.createCollection("yearlyEmissions")
        repo['aoconno8_dmak1112.yearlyEmissions'].insert_many(emissions_json)
        repo['aoconno8_dmak1112.yearlyEmissions'].metadata({'complete': True})
        print(repo['aoconno8_dmak1112.yearlyEmissions'].metadata())

        repo.logout()

        endTime = datetime.datetime.now()

        return {"start": startTime, "end": endTime}

    @staticmethod
    def provenance(doc=prov.model.ProvDocument(), startTime=None, endTime=None):
        '''
            Create the provenance document describing everything happening
            in this script. Each run of the script will generate a new
            document describing that invocation event.
            '''

        # Set up the database connection.
        client = dml.pymongo.MongoClient()
        repo = client.repo
        repo.authenticate('aoconno8_dmak1112', 'aoconno8_dmak1112')
        doc.add_namespace('alg','http://datamechanics.io/algorithm/aoconno8_dmak1112')  # The scripts are in <folder>#<filename> format.
        doc.add_namespace('dat','http://datamechanics.io/data/aoconno8_dmak1112')  # The data sets are in <user>#<collection> format.
        doc.add_namespace('ont','http://datamechanics.io/ontology#')  # 'Extension', 'DataResource', 'DataSet', 'Retrieval', 'Query', or 'Computation'.
        doc.add_namespace('log', 'http://datamechanics.io/log/')  # The event log.
        doc.add_namespace('databg', 'https://data.boston.gov/api')  # The event log.

        this_script = doc.agent('alg:aoconno8_dmak1112#yearlyEmissions',
                                {prov.model.PROV_TYPE: prov.model.PROV['SoftwareAgent'], 'ont:Extension': 'py'})
        resource = doc.entity('databg:3/action/datastore_search',
                              {'prov:label': 'Yearly Emissions Data', prov.model.PROV_TYPE: 'ont:DataResource'})
        get_yearlyEmissions = doc.activity('log:uuid' + str(uuid.uuid4()), startTime, endTime)
        doc.wasAssociatedWith(get_yearlyEmissions, this_script)
        doc.usage(get_yearlyEmissions, resource, startTime, None,
                  {prov.model.PROV_TYPE: 'ont:Retrieval', 'ont:Query': 'resource_id=$&limit=$'})
        yearlyEmissions = doc.entity('dat:aoconno8_dmak1112#yearlyEmissions',
                                 {prov.model.PROV_LABEL: 'Yearly Emissions', prov.model.PROV_TYPE: 'ont:DataSet'})
        doc.wasAttributedTo(yearlyEmissions, this_script)
        doc.wasGeneratedBy(yearlyEmissions, get_yearlyEmissions, endTime)
        doc.wasDerivedFrom(yearlyEmissions, resource, get_yearlyEmissions, get_yearlyEmissions, get_yearlyEmissions)

        repo.logout()

        return doc

# yearlyEmissions.execute()
# doc = yearlyEmissions.provenance()
# print(doc.get_provn())
# print(json.dumps(json.loads(doc.serialize()), indent=4))

## eof