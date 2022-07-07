from flask.json import JSONEncoder
from pymongo import MongoClient
from pymongo.errors import DuplicateKeyError
from flask import Flask, request, jsonify, redirect, Response
from datetime import datetime
import json
import uuid
import time
from bson import ObjectId,json_util, objectid
class JSONEncoder(json.JSONEncoder):
        def default(self,o):
            if isinstance(o,ObjectId):
                return str(o)
            return json.JSONEncoder.default(self, o)

client = MongoClient('mongodb://localhost:27017/')


db = client['DigitalNotes']

Users = db['Users']
Notes = db['Notes']
DigitalNotes = Flask(__name__)
users_sessions = {}
def create_session(username):
    user_uuid = str(uuid.uuid1())
    users_sessions[user_uuid] = (username, time.time())
    return user_uuid  

def is_session_valid(user_uuid):
    return user_uuid in users_sessions

@DigitalNotes.route('/createUser', methods=['POST'])
def create_user():
    
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not  "name" in data or not "password" in data or not "username" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')

    if Users.count_documents({'email':data['email']})>0:
        return Response("A user with the given email already exists", mimetype='application/json',status=400) 
    else:
        data['category']="user"
        Users.insert_one(data)
        return Response(data['name']+" was added to the Users", mimetype='application/json',status=200)

@DigitalNotes.route('/login', methods=['POST'])
def login():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not "password" in data or not "username" in data:
        return Response("Information incomplete",status=500,mimetype="application/json")
    if Users.count_documents( { '$and': [{'email':data['email']}, {'password':data['password']}]})>0:
        user_uuid=create_session(data['email'])
        res = {"uuid": user_uuid, "email": data['email']}
        return Response(json.dumps(res), mimetype='application/json',status=200) 
    else:
        return Response("Wrong username or password.",mimetype='application/json',status=400) 


@DigitalNotes.route('/createNote', methods=['POST'])
def create_Note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not  "name" in data or not "title" in data or not "text" in data or not "keyword" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    else:
        uuid = request.headers.get('Authorization')
        if  is_session_valid(uuid):
         u=Users.find_one({"email":data['email']})
         if u['category']=="user":
          date=datetime.now()
          d=date.strftime("%d/%m/%y")
          data['date']=d 
          Notes.insert_one(data)
          return Response("note is created "+data['date'], mimetype='application/json',status=200)  
        else:
          return Response("not authenticated", mimetype='application/json',status=400)       

    
          

@DigitalNotes.route('/searchNote', methods=['GET'])
def search_Note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
      u=Users.find_one({"email":data['email']})
      if u['category']=="user":
        if Notes.count_documents({'title':data['title']})>0:
         notes=list(Notes.find({'title':data['title']}))
         return Response(JSONEncoder().encode(notes), status=200, mimetype='application/json')
      else:             
         return Response("Notes were not found " ,status=400, mimetype='application/json')
    else:
        return Response("not authenticated", mimetype='application/json',status=400)       

    

@DigitalNotes.route('/searchNoteKey', methods=['GET'])
def search_NoteKey():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
      u=Users.find_one({"email":data['email']})
      if u['category']=="user":
        if Notes.count_documents({'keyword':data['keyword']})>0:
         notes2=list(Notes.find({'keyword':data['keyword']}))
         sort=sorted(notes2,key=lambda k: k['date'])
        return Response(JSONEncoder().encode(sort), status=200, mimetype='application/json')
      else:             
        return Response("Notes were not found " ,status=400, mimetype='application/json')
    else:
        return Response("not authenticated", mimetype='application/json',status=400)       




@DigitalNotes.route('/deleteNote', methods=['DELETE'])
def delete_note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
      u=Users.find_one({"email":data['email']})
      if u['category']=="user":

       if Notes.count_documents({'title':data['title']})==0:

        return Response("note was not found", mimetype='application/json',status=400) 
       else:
        Notes.delete_many({'$and': [{'title':data['title']} ]})
        return Response("Note was deleted", mimetype='application/json',status=200) 
    else:
        return Response("Not authenticated", mimetype='application/json',status=400) 
    

@DigitalNotes.route('/updateNote', methods=['PATCH'])
def update_Note():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "title" in data or not("text" in data or "keyword" in data or "title2" in data) :
        return Response("Information incomplete",status=500,mimetype='application/json')
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
      u=Users.find_one({"email":data['email']})
      if u['category']=="user":

    
       if Notes.count_documents({'title':data['title']})==0:
         return Response("Note dosn't exist", mimetype='application/json',status=400) 
       else:
            if "title2" in data:
                Notes.update_one({'title':data['title']},{"$set": {"title":data['title2']}})
            if "text" in data:
                Notes.update_one({'title':data['title']},{"$set": {"text":data['text']}})
            if "keyword" in data:
                Notes.update_one({'title':data['title']},{"$set": {"keyword":data['keyword']}})

            return Response("Note was updated", mimetype='application/json',status=200) 
    else : 
            return Response("not authenticated", mimetype='application/json',status=400) 

@DigitalNotes.route('/sortNotes', methods=['GET'])
def sort_Notes():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "order" in data  :
        return Response("Information incomplete",status=500,mimetype='application/json')
    if data['order']=='new':
        notes3=list(Notes.find().sort("date", 1))
        return Response(JSONEncoder().encode(notes3), status=200, mimetype='application/json')
    elif data['order']=='old' : 
        notes3=list(Notes.find().sort("date" ,-1))
        return Response(JSONEncoder().encode(notes3), status=200, mimetype='application/json')
    else :
       return Response("enter a new value", status=200, mimetype='application/json')
    


@DigitalNotes.route('/deleteUser', methods=['DELETE'])
def deleteUser():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not  "email" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    uuid = request.headers.get('Authorization')
    if  is_session_valid(uuid):
      u=Users.find_one({"email":data['email']})
      if u['category']=="user":

    
        if Users.count_documents({'email':data['email']})!=0:
            
            Notes.delete_many({'email':data['email']})
            Users.delete_one({'email':data['email']})
            return Response("user was deleted", status=200, mimetype='application/json')
        else:
            return Response("the user Dosn't exist" ,status=400, mimetype='application/json')
    else :
            return Response("not authenticated", mimetype='application/json',status=400) 


@DigitalNotes.route('/createAdmin', methods=['POST'])
def create_admin():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not "email" in data or not  "username" in data or not "password" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    
    
     
    if Users.count_documents({'email':data['email']})>0:
         return Response("A admin with the given email already exists", mimetype='application/json',status=400) 
    else:
        data["category"]="admin"
        Users.insert_one(data)
        return Response(data['username']+" was added to the Users", mimetype='application/json',status=200)


@DigitalNotes.route('/deleteAdmin', methods=['DELETE'])
def deleteAdmin():
    # Request JSON data
    data = None 
    try:
        data = json.loads(request.data)
    except Exception as e:
        return Response("bad json content",status=500,mimetype='application/json')
    if data == None:
        return Response("bad request",status=500,mimetype='application/json')
    if not  "username" in data:
        return Response("Information incomplete",status=500,mimetype='application/json')
    if Users.count_documents({'username':data['username']})!=0:
            data["category"]="admin"
            Users.delete_one({'username':data['username']})
            return Response("user was deleted", status=200, mimetype='application/json')
    else:
            return Response("the user Dosn't exist" ,status=400, mimetype='application/json')

    
   

     

    

    
if __name__== '__main__' :
    DigitalNotes.run(debug=True,host='0.0.0.0',port=5000)