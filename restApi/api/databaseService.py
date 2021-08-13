from py2neo import Graph, Node, Relationship
from py2neo.matching import *
import json
class DatabaseService():
	"""Handles all database transactions """
	def __init__(self):
		super(DatabaseService, self).__init__()

		with open('/home/graphSearchEngine/restApi/config.json') as dataFile:
			self.config = json.load(dataFile)
			self.connectToDB()
	
	# drops the database
	def dropDatabase(self):
		self.graph.delete_all()
			
	# connects to the database based on the config in config.json.
	# todo: handle exceptions
	def connectToDB(self):
		try:
			# self.graph = Graph(self.config['bolt_url'], auth=(self.config['neo4j_username'], self.config['neo4j_password']))
			self.graph = Graph(self.config['bolt_url'], auth=(self.config['neo4j_username'], self.config['neo4j_password']))
		except Exception as e:
			raise e

	def createNode(self, type, properties):
		node = Node(type, **properties)
		self.graph.create(node)
		return node
	
	# looks for a matching node. if it doesn't exits, creates it and returns it
	def getNode(self, type, properties):
		nodes = NodeMatcher(self.graph)
		node = nodes.match(type, **properties).first()
		if not node:
			node = self.createNode(type, properties)
		return node
	# executes a cypher query and returns the resultset
	# todo: handle exceptions 
	def executeQuery(self, query):
		try:
			return self.graph.run(query)
		except Exception as e:
			raise e
	# creates a relation between two nodes
	def createRelation(self, node1, node2, relationType):
		relation = Relationship.type(relationType)
		self.graph.merge(relation(node1, node2))

	# generates the cypher query and retrieves it's results from the Neo4j database
	def getRetrieval(self, params):
		source = 'match (p:Product) '
		relation = '-['+ params['relationType'] + ']-> '
		target = ' (x:'+ params['targetEntityType'] + ') '
		

		where = ' where '
		if params['sourceEntity']:
			where += ' p.name = "'+ params['sourceEntity'] + '"'
		if params['targetEntity']:
			if params['sourceEntity']:
				where += ' and '
			where += ' x.name contains "'+ params['targetEntity'] + '"'

		returnClause= ' return p,x'
		if not params['sourceEntity'] and not params['targetEntity']:
			query = source + relation + target + returnClause
		else:
			query = source + relation + target + where + returnClause
		print(query)
		result = self.graph.run(query, {"sourceEntity": params['sourceEntity'], 'relation': params['relationType']})
		return result