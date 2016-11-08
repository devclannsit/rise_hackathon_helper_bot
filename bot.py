import alchemyapi, json
from nltk import word_tokenize,Text,pos_tag
from nltk.corpus import wordnet
from flask import Flask, jsonify, request
from flask_restful import Resource, Api
from flask_mysqldb import MySQL

main_verbs = ["get", "find", "renew", "register", "pay", "claim", "want"]
verb_dict = {}
last_main_verb = None

api = alchemyapi.AlchemyAPI()

def default_train():
	global main_verbs
	global verb_dict

	for verb in main_verbs:
		suggestions = wordnet.synset(str(verb) + ".v.01").lemma_names()
		suggestions.remove(verb)
		verb_dict.update({verb: suggestions})

def train(query):
	global verb_dict
	global last_main_verb

	tokens = word_tokenize(query)
	text = Text(tokens)
	tags = pos_tag(text)

	result = {}
	verbs = []
	temp_verbs = []

	for i in range(len(tags)):
		if "VB" in str(tags[i][1]):
			if tags[i][0] == 'i':
				continue
			
			suggestions = wordnet.synset(str(tags[i][0]) + ".v.01").lemma_names()
			
			exist = False
			for x in verb_dict.keys():
				if list(set(suggestions) & set(verb_dict[x])) or list(set(suggestions) & set([x])) or tags[i][0] == x:
					arr = verb_dict[x]
					arr.append(last_main_verb)
					verb_dict.update({x : arr})
					exist = True
					break
			if exist:
				verbs.append(tags[i][0])
			else:
				last_main_verb = tags[i][0]
				return {"message": "Sorry, I could'nt understand. Can you please give only keywords?"}
			
			result.update({"intent" : verbs})
			break

	return result

def get_main_verb(query):
	global verb_dict
	global last_main_verb

	tokens = word_tokenize(query)
	text = Text(tokens)
	tags = pos_tag(text)

	result = {}
	verbs = []
	temp_verbs = []

	for i in range(len(tags)):
		if "VB" in str(tags[i][1]):
			if tags[i][0] == 'i':
				continue
			try:
				suggestions = wordnet.synset(str(tags[i][0]) + ".v.01").lemma_names()
			except:
				suggestions = []
			
			exist = False
			for x in verb_dict.keys():
				if list(set(suggestions) & set(verb_dict[x])) or list(set(suggestions) & set([x])) or tags[i][0] == x:
					exist = True
					break
			if exist:
				verbs.append(tags[i][0])
			else:
				last_main_verb = tags[i][0]
				continue
			
			result.update({"intent" : verbs})

	if len(result.keys()) == 0:
		return {"message": "Sorry, try again with better keywords. No results found."}

	keys = api.keywords("text", query)["keywords"]
	keywords = [keys[0]["text"]]
	ctr = 0
	
	for key in keys:
		if ctr == 0:
			ctr += 1
			continue
		
		exist = False
		
		for x in verb_dict.keys():
			if key["text"] in verb_dict[x] or key["text"] == x:
				exist = True
				break
		
		if exist:
			keywords.append(key["text"])

	result.update({"keywords": keywords})

	return result

def main():
	default_train()
	global last_main_verb

	app = Flask(__name__)
	
	mysql = MySQL(app)
	server = Api(app)
	
	class receive_from_site(Resource):
		def post(self):
			data = str(request.get_data())
			query = data.split("=")[1]
			query = query.replace("+", " ")
			resp = get_main_verb(query)
			return jsonify({"result": resp})

	server.add_resource(receive_from_site, "/send")
	
	app.run(debug = True)

if __name__ == '__main__':
	main()