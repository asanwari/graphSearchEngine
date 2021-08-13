import pdfplumber
import csv
import re
import json
import os
class Extractor():
	"""Extracts the document """
	def __init__(self):
		super(Extractor, self).__init__()
		with open('/home/graphSearchEngine/restApi/config.json') as configFile:
			self.config = json.load(configFile)
			self.basePath = self.config['data_dir']

		self.products = {}
		self.substance = set()
		self.regulations = set()
		self.productSet = set()
		with open(self.basePath + 'products.csv',encoding="utf8") as file:
			reader = csv.reader(file, delimiter='\t', quotechar="'")
			productList = list(reader)
			productList.pop(0)
			self.productList = set([x[0].strip().lower() for x in productList])
		self.regulationRegexes = [re.compile(x) for x in [r'($|\s){0,1}([0-9]{4}/[0-9]{2,4}/[A-Z]{2})($|\s)', r'($|\s){0,1}([0-9]{4}/[0-9]{4})($|\s)']]
		self.productRegex = re.compile(r'([a-zA-Z]+)(\u00AE)')

	# This is the main extraction flow. It traverses over the document folder, extracts data and writes results to json
	def extractFiles(self):
		directory = self.basePath+ 'documents'
		for file in os.listdir(directory):
			self.extractData(os.path.join(directory, file))
			self.writeToJsonFile()

	# extracts data from a single pdf file.
	def extractData (self, filePath):
		with pdfplumber.open(filePath) as pdf:
			for pageNum in range(len(pdf.pages)):
				page = pdf.pages[pageNum]
				lines = page.extract_text(x_tolerance=1, y_tolerance=2).split('\n')
				products = []
				i = 0
				while i < len(lines):
					line = lines[i].strip()
					if not self.validLineCheck(line):
						i+=1
						continue
					if 'This statement applies to the following product lines:' in line:
						i+=1
						# skip the blank lines
						while not self.validLineCheck(lines[i]):
							i+=1
						# add lines to product until blank lines are reached
						while self.validLineCheck(lines[i]):
							products.append(lines[i])
							i+=1
						self.extractProducts(products)
						continue
					self.extractSubstances(line)

					self.extractRegulations(line)
					
					i+=1
		
		self.addToJson()
		self.resetTempVars()

	# adds the file's extracted data to the json file. All files make up one json
	def addToJson(self):
		for product in self.productSet:
			if product in self.products:
				regulation = set(self.products[product]['regulations'])
				regulation.update(self.regulations)
				self.products[product]['regulations'] = list(regulation)

				substances = set(self.products[product]['is_without'])
				substances.update(self.substance)
				self.products[product]['is_without'] = list(substances)
			else:
				self.products[product] = {}
				self.products[product]['regulations'] = list(self.regulations)
				self.products[product]['is_without'] = list(self.substance)


	def writeToJsonFile(self):
		with open(self.basePath+'products.json', 'w') as fp:
			json.dump(self.products, fp)

	# resets the temp vars for next pdf file
	def resetTempVars(self):
		self.substance = set()
		self.regulations = set()
		self.productSet = set()
	# checks for empty lines
	def validLineCheck(self, line):
		if len(line.strip()) == 0:
			return False
		return True

	# extracts substance information
	def extractSubstances(self,line):
		line = line.lower()
		if 'product information:' in line.lower():
			self.substance.add('-'.join(line.split()[2:]))
			
	# extracts regulation information
	def extractRegulations(self,line):
		for regex in self.regulationRegexes:
			matches = regex.findall(line)
			matches = [match[1] for match in matches]
			if len(matches) > 0:
				self.regulations.update(matches)
		
		
	# extracts product information
	def extractProducts(self, products):
		self.productSet = set()
		for product in products:
			matches = self.productRegex.findall(product)
			for match in matches:
				candidate = match[0].strip().lower()
				if candidate in self.productList:
					self.productSet.add(candidate)


def main():
	ext = Extractor()
	ext.extractFiles()

if __name__ == '__main__':
	main()