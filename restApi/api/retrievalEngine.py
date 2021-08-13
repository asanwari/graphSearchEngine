
import spacy
import re
import numpy as np
from fuzzywuzzy import process
import json
import csv
import string
from api.databaseService import DatabaseService
class RetrievalEngine():
	"""Populates the neo4j Graph """
	def __init__(self):
		super(RetrievalEngine, self).__init__()
		self.sourceEntityType = 'Product'
		self.sourceEntity = None
		self.targetEntityType = None
		self.targetEntity = None
		self.relationType = None
		self.query = None
		self.nlpDoc = None
		self.productNameCorrected = False


		self.databaseService = DatabaseService()
		# get fuzzy match threshold
		with open('/home/graphSearchEngine/restApi/config.json') as configFile:
			self.config = json.load(configFile)
			self.dataPath = self.config['data_dir']
			self.fuzzyThreshold = self.config['fuzzy_match_threshold']

		with open(self.dataPath + 'products.csv',encoding="utf8") as file:
			reader = csv.reader(file, delimiter='\t', quotechar="'")
			productList = list(reader)
			productList.pop(0)
			self.productList = set([x[0].strip().lower() for x in productList])

		self.nlp =  spacy.load("en_core_web_sm")

		self.regulationRegexes = [re.compile(x) for x in [r'($|\s){0,1}([0-9]{4}/[0-9]{2,4}/[A-Z]{2})($|\s)', r'($|\s){0,1}([0-9]{4}/[0-9]{4})($|\s)']]
		# we can add more words which are used to describe our relations
		regulationWords = 'complies follows regulation regulations'
		self.regulationWords = set(self.getLemmatized(regulationWords))
		
		substanceWords = 'contain has have without'
		self.substanceWords = set(self.getLemmatized(substanceWords))

		self.productWords = set(['products', 'product'])
	

	# looks for the name of a product. if no name is found, it resorts to fuzzy matching
	def productHeuristic(self):
		nouns = []
		# exact matching in productList
		# O(n) as set lookup is O(1)
		for word in self.nlpDoc:
			if word.text in self.productList:
				self.sourceEntity = word.text
				return True
			
			if word.pos_ == 'PROPN' or word.pos_ == 'NOUN':
				nouns.append(word.text)

			
		# if there is a noun called product or products, it means the query is about all products. No need to search further
		if 'product' in nouns or 'products' in nouns:
			return True		
		# if exact match not found, resort to fuzzy matching.
		# fuzzy match all the nouns in the qurey against the product list. 
		# this has a fairly large time complexity. I would not do this in real life.
		# I am retuning the first fuzzy match that satisfies the threshold


		for noun in nouns:
			fuzzyMatch = process.extractOne(noun, self.productList)
			if fuzzyMatch[1] > self.fuzzyThreshold:
				self.sourceEntity = fuzzyMatch[0]
				self.productNameCorrected = True
				return True
		return False

		
	# assuming that the substance is always mentioned after the substance words, I am 
	# using it as a valid substance
	def substanceHeuristic(self):
		idx = 0
		found = False
		for word in self.nlpDoc:
			if word.lemma_ in self.substanceWords:
				found = True
				idx+=1
				break
			idx += 1
		self.targetEntity = '-'.join(str(word) for word in self.nlpDoc[idx:])
		self.targetEntityType = 'Substance'
		self.relationType = 'IS_WITHOUT'
		return found

	# main retrieval function. sequentally does all the tasks required for retrieval and returns the result
	def retrieve(self,query):
		self.query = query
		self.nlpfy(query)
		self.productHeuristic()


		if not self.regulationHeuristic(query):
			self.substanceHeuristic()
		
		results = self.getResults()
		self.resetVariables()
		return results


	# heuristic function to extract regulation
	def regulationHeuristic(self, text):
		for regex in self.regulationRegexes:
			matches = regex.findall(text)
			matches = [match[1] for match in matches]
			if len(matches) > 0:
				self.targetEntityType = 'Regulation'
				# for now, I am only matching against the first detected regulation. in general, we can have a list of regulations.
				# eg. "which products comply with regulation x, regulation y, regulation c"
				# This engine can't do that yet
				self.targetEntity = matches[0]
				self.relationType = 'COMPLIES'
				return True
		for word in self.nlpDoc:
			if word.lemma_ in self.regulationWords:
				self.relationType = 'COMPLIES'
				self.targetEntityType = 'Regulation'
				return True
		return False

	# reset the variables for next search
	def resetVariables (self):
		self.sourceEntityType = 'Product'
		self.sourceEntity = None
		self.targetEntityType = None
		self.targetEntity = None
		self.relationType = None
		self.query = None
		self.nlpDoc = None 
		self.productNameCorrected = False

	# helper method: nlpfies the query
	def nlpfy(self, text):
		self.nlpDoc = self.nlp(text)
		# remove punctuation
		self.nlpDoc = [t for t in self.nlpDoc if t.text not in string.punctuation]


	# returns the lemmatized version of the text
	def getLemmatized(self, text):
		self.nlp.get_pipe('lemmatizer')
		words = self.nlp(text)
		return [token.lemma_ for token in words]

	# queries the databaseService for the results, packages the results and returns them
	def getResults(self):
		params = {'sourceEntity' : self.sourceEntity, 'sourceEntityType': self.sourceEntityType, 'targetEntity' : self.targetEntity,'targetEntityType': self.targetEntityType, 'relationType':self.relationType}
		# return params
		matches = self.databaseService.getRetrieval(params)
		resultSet = []
		result = {}
		result['queryAnalysis'] = params
		result['queryAnalysis']['productNameCorrected'] = self.productNameCorrected
		
		for match in matches:
			curr = {}
			curr['product'] = match[0]['name']
			curr['relation'] = params['relationType']
			curr['target'] = match[1]['name']
			resultSet.append(curr)
		result['retrievalResult'] = resultSet
		return result


def main():
	retrievalEngine = RetrievalEngine()
	# retrievalEngine.retrieve('which products comply with regulation 1005/2009/EC')
	retrievalEngine.retrieve('products containing latex')
	

if __name__ == '__main__':
	main()