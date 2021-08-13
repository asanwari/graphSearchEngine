from flask import Flask,request,jsonify
import markdown
import json
from api.retrievalEngine import RetrievalEngine
from api.extractor import Extractor
from api.graphPopulator import GraphPopulator
from api.databaseService import DatabaseService

app = Flask(__name__)

@app.route("/", methods=['GET'])
def hello_world():
    return 'I am alive!'

@app.route("/checkDatabaseConnection", methods=['GET'])
def checkDatabaseConnection():
    try:
        dbService = DatabaseService()
        return 'connection successful'
    except Exception as e:
        return "Couldn't connect to database" + str(e) , 500

@app.route("/dropDatabase", methods=['GET'])
def dropDatabase():
    try:
        dbService = DatabaseService()
        dbService.dropDatabase()
        return 'Database Dropped'
    except Exception as e:
        return "Couldn't connect to database" + str(e) , 500

    
@app.route("/getQuery", methods=['POST'])
def getQuery():
    try:
        retrievalEngine = RetrievalEngine()
        data = request.json
        return jsonify(retrievalEngine.retrieve(data['query']))
    except Exception as e:
        return "Some error occured: " + str(e), 500



@app.route("/extract", methods=['get'])
def extract():
    try:
        ext = Extractor()
        ext.extractFiles()
        return 'Extraction Complete'
    except Exception as e:
        return str(e), 500

@app.route("/constructGraph", methods=['get'])
def constructGraph():
    try:
        populator = GraphPopulator()
        populator.populateGraph()
        return 'graph Constructed'
    except Exception as e:
        return srt(e), 500

