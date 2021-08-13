from py2neo import Graph, Node, Relationship
import json
from api.databaseService import DatabaseService
class GraphPopulator():
	"""Populates the neo4j Graph """
	def __init__(self):
		super(GraphPopulator, self).__init__()
		self.databaseService = DatabaseService()
		with open('/home/graphSearchEngine/restApi/config.json') as dataFile:
			self.config = json.load(dataFile)
			self.jsonPath = self.config['extracted_json_path']
			

	# populates the graph
	def populateGraph(self):		
		with open(self.jsonPath) as jsonFile:
			products = json.load(jsonFile)
		
		for product in products:
			productNode = self.databaseService.getNode('Product', {'name': product})
			for regulation in products[product]['regulations']:
				regulationNode = self.databaseService.getNode('Regulation', {'name': regulation})
				self.databaseService.createRelation(productNode, regulationNode, 'COMPLIES')
			for substance in products[product]['is_without']:
				substanceNode = self.databaseService.getNode('Substance', {'name': substance})
				self.databaseService.createRelation(productNode, substanceNode, 'IS_WITHOUT')


def main():
	populator = GraphPopulator()
	populator.populateGraph()

if __name__ == '__main__':
	main()