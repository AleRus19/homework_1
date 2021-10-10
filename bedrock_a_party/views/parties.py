from flakon import JsonBlueprint
from flask import abort, json, jsonify, request


from bedrock_a_party.classes.party import CannotPartyAloneError, ItemAlreadyInsertedByUser, NotExistingFoodError, NotInvitedGuestError, Party

parties = JsonBlueprint('parties', __name__)

_LOADED_PARTIES = {}  # dict of available parties
_PARTY_NUMBER = 0  # index of the last created party


@parties.route("/parties", methods=['GET', 'POST'])
def all_parties():
    result = None

    if request.method == 'POST':

        # create a party
        try:
            # save in result the party identifier
            result = create_party(request)
        except CannotPartyAloneError as e:
            result = jsonify({'msg': e.__str__()}), 400 # error 400: Bad Request
    elif request.method == 'GET':

        # retrieve all scheduled parties
        result = get_all_parties()

    return result



@parties.route("/parties/loaded", methods=['GET'])
def loaded_parties():

    # return the number of parties currently loaded in the system
    
    return get_number_loaded_parties()




@parties.route("/party/<id>", methods=['GET', 'DELETE'])
def single_party(id):
    global _LOADED_PARTIES
    result = ""

    # check if the party identified by <id> is an existing one
    exists_party(str(id))

    if 'GET' == request.method:
        # retrieve the party identified by <id> 
        result = jsonify(_LOADED_PARTIES[str(id)].serialize())

    elif 'DELETE' == request.method:
        # delete the party identified by <id>
        _LOADED_PARTIES.pop(str(id))
        result = jsonify({'msg': "Party deleted!"})
        
    return result



@parties.route("/party/<id>/foodlist", methods=['GET'])
def get_foodlist(id):
    global _LOADED_PARTIES
    result = ""

    # check if the party identified by <id> is an existing one
    exists_party(str(id))

    if 'GET' == request.method:
        # retrieve food-list of the party identified by <id>
        result = jsonify({'foodlist':_LOADED_PARTIES[str(id)].get_food_list().serialize()})

    return result


@parties.route("/party/<id>/foodlist/<user>/<item>", methods=['POST', 'DELETE'])
def edit_foodlist(id, user, item):
    global _LOADED_PARTIES

    # check if the party identified by <id> is an existing one
    exists_party(str(id))

    # retrieve the party identified by <id>
    party = _LOADED_PARTIES[str(id)]

    result = ""

    if 'POST' == request.method:
        # add the <item> brought by <user> to the food-list of the party <id>
        try:
            party.add_to_food_list(item, user)
            result = jsonify({'food':str(item), 'user':str(user)})
        except NotInvitedGuestError as e1:
            result = jsonify({'msg': e1.__str__()}), 401 # error 401: 401 Unauthorized Access
        except ItemAlreadyInsertedByUser as e2:
            result = jsonify({'msg': e2.__str__()}), 400 # error 400: Bad Request
    
    if 'DELETE' == request.method:
        # remove the given <item> brought by <user> from the food-list of the party <id>
        try:
            party.remove_from_food_list(item, user)
            result = jsonify({'msg':"Food deleted!"})
        except NotExistingFoodError as e: 
            result = jsonify({'msg': e.__str__()}), 400 # error 400: Bad Request
            
    return result


#
# These are utility functions. Use them, DON'T CHANGE THEM!!
#

def create_party(req):
    global _LOADED_PARTIES, _PARTY_NUMBER

    # get data from request
    json_data = req.get_json()

    # list of guests
    try:
        guests = json_data['guests']
    except:
        raise CannotPartyAloneError("you cannot party alone!")

    # add party to the loaded parties lists
    _LOADED_PARTIES[str(_PARTY_NUMBER)] = Party(_PARTY_NUMBER, guests)
    _PARTY_NUMBER += 1

    return jsonify({'party_number': _PARTY_NUMBER - 1})


def get_all_parties():
    global _LOADED_PARTIES

    return jsonify(loaded_parties=[party.serialize() for party in _LOADED_PARTIES.values()])


def exists_party(_id):
    global _PARTY_NUMBER
    global _LOADED_PARTIES

    if int(_id) > _PARTY_NUMBER:
        abort(404)  # error 404: Not Found, i.e. wrong URL, resource does not exist
    elif not(_id in _LOADED_PARTIES):
        abort(410)  # error 410: Gone, i.e. it existed but it's not there anymore

        
def get_number_loaded_parties():
    global _LOADED_PARTIES
    
    return jsonify({'loaded_parties': len(_LOADED_PARTIES)})
