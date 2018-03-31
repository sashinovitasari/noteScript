import os

os.environ["GOOGLE_APPLICATION_CREDENTIALS"] = "TryNLP-f5ba5437ac09.json"

from google.cloud import language
from google.cloud.language import enums
from google.cloud.language import types

client = language.LanguageServiceClient()

import json
import re
import six

pos_tag = ('UNKNOWN', 'ADJ', 'ADP', 'ADV', 'CONJ', 'DET', 'NOUN', 'NUM',
			'PRON', 'PRT', 'PUNCT', 'VERB', 'X', 'AFFIX')

def formPhrase(tokens, depend):
	dependIndex = -1
	left = []
	right = []
	for i in range(len(tokens)):
		if tokens[i].dependency_edge.head_token_index == depend:
			if i < depend:
				left = left + formPhrase(tokens, i)
			else:
				right=right + formPhrase(tokens, i)

	return left + [depend] + right

def createVerbObj(tokens, indexes):
	verb = ""
	firstVerbSeen = False
	obj = ""
	for index in indexes:
		if not firstVerbSeen and pos_tag[tokens[index].part_of_speech.tag] == 'VERB':
			verb += tokens[index].text.content + " "
		else:
			firstVerbSeen = True
			obj += tokens[index].text.content + " "
	return verb, obj

def breakToStruct(tokens, startI, endI):
	print("start, end: ",startI, endI)
	rootIndex = -1
	#subject = ""
	phrases = []

	for i in range(startI, endI):	# find the root
		#subject = subject + tokens[i].text.content + " "
		if str(tokens[i].dependency_edge.label) == '54':	# 54 IS ROOT
			rootIndex = i 
			break
	
	for i in range(startI, endI):	# find the formPhrase from word that depend on rootIndex
		if i == rootIndex:
			continue
		if tokens[i].dependency_edge.head_token_index == rootIndex:
			phrases.append(formPhrase(tokens, i))


	temp = []
	for i in range(len(phrases)): # remove moreover, this kind of aux phrase
		allAuxPunc = True
		for j in phrases[i]:
			if pos_tag[tokens[i].part_of_speech.tag] != 'ADV' and pos_tag[tokens[i].part_of_speech.tag]!= 'PUNCT': # although and shit
				allAuxPunc = False

		if not allAuxPunc:
			temp.append(phrases[i])

	phrases = temp

	subject = ""
	subjectToken = phrases[0]
	print(phrases)
	for i in subjectToken:
		subject += tokens[i].text.content + " "

	result = {subject:{}}

	verb = ""

	for i in range(startI, endI):	# append aux verb 
		if tokens[i].dependency_edge.head_token_index == rootIndex:
			if pos_tag[tokens[i].part_of_speech.tag] == 'VERB':
				if str(tokens[i].dependency_edge.label) == '9': # 9 is aux
					verb += tokens[i].text.content + " "

	verb += tokens[rootIndex].text.content

	for i in phrases[1]:
		validAux = True
		if tokens[i].dependency_edge.head_token_index == rootIndex and pos_tag[tokens[i].part_of_speech.tag] == 'VERB' and str(tokens[i].dependency_edge.label) == '9': # 9 is aux
			pass
		else:
			validAux = False

	if validAux:
		del phrases[1]


	rootVerb = {}

	rootVerb[verb] = ""
	print(phrases)
	for i in phrases[1]:
		rootVerb[verb] += tokens[i].text.content+ " "


	for k in result:	# k is key, should only be one
		result[k] = rootVerb

	#pos_tag = ('UNKNOWN', 'ADJ', 'ADP', 'ADV', 'CONJ', 'DET', 'NOUN', 'NUM',
	#		   'PRON', 'PRT', 'PUNCT', 'VERB', 'X', 'AFFIX')

	for i in range(2, len(phrases)):	# start at 2, 0 is subject, 1 is 1st object, rootindex is 1st verb
		isDetOrPunct = False
		count = 0	# nth of item in one phrase
		for j in phrases[i]:
			if pos_tag[tokens[j].part_of_speech.tag] == 'CONJ':#or pos_tag[tokens[j].part_of_speech.tag] == 'PUNCT':
				isDetOrPunct = True
				break
			if count == 0 and pos_tag[tokens[j].part_of_speech.tag] == 'VERB':
				verb, obj = createVerbObj(tokens, phrases[i])
				print("verb: ", verb, "obj: ",obj)
				for k in result:
					result[k][verb] = obj 	# insert new verb and object 
			break
			count += 1

		if isDetOrPunct:
			continue 




	#print(subject)	
	#print(result)

	return result

	'''
	result = {}
	result["subject"] = phrases[0]
	result["verb"] = []
	result["verb"].append(tokens[rootIndex].text.content)
	'''


def entities_text(text):
	"""Detects entities in the text."""
	client = language.LanguageServiceClient()

	if isinstance(text, six.binary_type):
		text = text.decode('utf-8')

	# Instantiates a plain text document.
	document = types.Document(
		content=text,
		type=enums.Document.Type.PLAIN_TEXT)

	# Detects entities in the document. You can also analyze HTML with:
	#   document.type == enums.Document.Type.HTML
	entities = client.analyze_entities(document).entities

	# entity types from enums.Entity.Type
	entity_type = ('UNKNOWN', 'PERSON', 'LOCATION', 'ORGANIZATION',
				   'EVENT', 'WORK_OF_ART', 'CONSUMER_GOOD', 'OTHER')
	# print(entities)

	result = {}
	for entity in entities:
		result[entity.name] = entity.salience
		'''
		print('=' * 20)
		print(u'{:<16}: {}'.format('name', entity.name))
		print(u'{:<16}: {}'.format('type', entity_type[entity.type]))
		print(u'{:<16}: {}'.format('metadata', entity.metadata))
		print(u'{:<16}: {}'.format('salience', entity.salience))
		print(u'{:<16}: {}'.format('wikipedia_url',
			entity.metadata.get('wikipedia_url', '-')))
		'''
	print(result)
	return result


def syntax_text(text):
	"""Detects syntax in the text."""
	client = language.LanguageServiceClient()

	if isinstance(text, six.binary_type):
		text = text.decode('utf-8')

	# Instantiates a plain text document.
	document = types.Document(
		content=text,
		type=enums.Document.Type.PLAIN_TEXT)

	# Detects syntax in the document. You can also analyze HTML with:
	#   document.type == enums.Document.Type.HTML
	result = client.analyze_syntax(document)
	tokens = result.tokens
	print(result)
	# part-of-speech tags from enums.PartOfSpeech.Tag
	pos_tag = ('UNKNOWN', 'ADJ', 'ADP', 'ADV', 'CONJ', 'DET', 'NOUN', 'NUM',
			   'PRON', 'PRT', 'PUNCT', 'VERB', 'X', 'AFFIX')

	for token in tokens:
		print(u'{}: {}'.format(pos_tag[token.part_of_speech.tag],
							   token.text.content))

	start = 0
	sentences = []
	saliences = []
	# print("type of token:" + str(type(tokens)))
	count = 0	# count follows the number of sentence it is on
	for i in range(len(tokens)):
		#print ("i, start:", i, start)
		if tokens[i].text.content == '.' or tokens[i].text.content == '?':
			sentenceFrac = breakToStruct(tokens, start, i+1)	# break to frac structure
			sentences.append(sentenceFrac)
			sent = result.sentences[count].text.content
			print("sent: ", sent)
			salience = entities_text(sent)		# change get salience analysis on individual sentence

			saliences.append(salience)
			start = i + 1
			count += 1

	print("sentences: ", sentences)
	print("saliences:", saliences)

	# assert len(sentences) == len(saliences)




	# result = []
	'''
	tokenDependReverse = list(range(len(tokens)))
	for i in range(len(tokens)):
		targetIndex = tokens[i].dependency_edge.head_token_index
		tokenDependReverse[targetIndex] = i


	print(tokenDependReverse)
	# get the last punc
	lastPunc = tokens[len(tokens)-1]

	firstDepend = lastPunc["dependency_edge"]["head_token_index"]

	endString = ""

	for i in range(firstDepend):
		endString+= token[i]["text"]["content"]
		endString+=" "

	endString += '\n\t'

	for i in range(firstDepend, len(tokens)):
	'''


#str1 = "black hole is a region and has a gravitational field. Region is a space and blocks"
str1 = "A galaxy has black holes. The universe contains black holes. Black holes are regions and have strong gravity. Region is space and doesn't let light escape."
#str1 = "The boundary of the region from which no escape is possible is called the event horizon."
#str1= "Moreover, black holes have strong gravity."
#str1 = "black holes are regions and have strong gravity. region is a space and does not let light escape. "
syntax_text(str1)

# entities_text(str1)

