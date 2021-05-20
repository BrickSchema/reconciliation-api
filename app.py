from flask import Flask, request
from flask_jsonpify import jsonify
from abbrmap import abbrmap as tagmap
import json
import brickschema
import re
import uuid
from flask_caching import Cache

#TODO - can flask tell us this?
service_url_base = "http://localhost:5000"

config = {
    "DEBUG": True,          # some Flask specific configs
    "CACHE_TYPE": "simple", # Flask-Caching related configs
    "CACHE_DEFAULT_TIMEOUT": 3600
}
app = Flask(__name__)
# tell Flask to use the above defined config
app.config.from_mapping(config)
cache = Cache(app)

metadata = {
    "name": "Brick Reconciliation Service",
    "versions": ["0.2"],
    "defaultTypes": [
        {"id": "EquipmentClass", "name": "EquipmentClass"},
        {"id": "PointClass", "name": "PointClass"}
    ],
  "extend": {
  "propose_properties": {
    "service_url": service_url_base + "/reconcile",
    "service_path": "/properties"
  },
  "property_settings": [
    {
      "name": "limit",
      "label": "Limit",
      "type": "number",
      "default": 0,
      "help_text": "Maximum number of values to return per row (0 for no limit)"
    },
    {
      "name": "content",
      "label": "Content",
      "type": "select",
      "default": "literal",
      "help_text": "Content type: ID or literal",
      "choices": [
        {
          "value": "id",
          "name": "ID"
        },
        {
          "value": "literal",
          "name": "Literal"
        }
      ]
    }
  ]
  }
}

props_per_type = {
   'PointClass': [ {"id": "ExtendedBrickString", "name": "ExtendedBrickString"}, {"id": "BrickSpace", "name": "BrickSpace"}],
   'EquipClass': [ {"id": "ExtendedBrickString", "name": "ExtendedBrickString"},], 
}

inf = brickschema.inference.TagInferenceSession(approximate=True)


def flatten(lol):
    """flatten a list of lists"""
    return [x for sl in lol for x in sl]


def resolve(q):
    """
    q has fields:
    - query: string of the label that needs to be converted to a Brick type
    - type: optional list of 'types' (e.g. "PointClass" above)
    - limit: optional limit on # of returned candidates (default to 10)
    - properties: optional map of property idents to values
    - type_strict: [any, all, should] for strictness on the types returned
    """
    limit = int(q.get('limit', 10))
    # break query up into potential tags
    tags = map(str.lower, re.split(r'[.:\-_ ]', q.get('query', '')))
    tags = list(tags)

    # HACK
    space_tags = [x for x in tags if 'room' in x]
    tags = [x for x in tags if 'room' not in x]
    equip_tags = [x for x in tags if 'tstat' in x]
    tags = [x for x in tags if 'tstat' not in x]
    final_id = tags[-1]

    brick_tags = flatten([tagmap.get(tag.lower(), [tag]) for tag in tags])

    if q.get('type') == 'PointClass':
        brick_tags += ['Point']
    elif q.get('type') == 'EquipmentClass':
        brick_tags += ['Equipment']

    res = []
    most_likely, leftover = inf.most_likely_tagsets(brick_tags, limit)
    for ml in most_likely:
        id = uuid.uuid4()
        res.append({
            'id': str(id),
            'name': ml,
            'score': (len(brick_tags) - len(leftover)) / len(brick_tags),
            'match': len(leftover) == 0,
            'type': [{"id": "PointClass", "name": "PointClass"}],
        })
        extended_str = ''
        space_str = 'Space'
        if len(space_tags) > 0:
           prefixed = ["BrickSpace:" + x for x in space_tags]
           space_str = ''.join(prefixed)
           if len(space_str) == 0:
              space_str = "BrickSpace:Unknown"
           extended_str = extended_str + space_str
        if len(equip_tags) > 0:
           prefixed = ["BrickEquip:" + x for x in equip_tags]
           extended_str = extended_str + ":"+ ''.join(prefixed)  
        extended_str = extended_str + ":" + ml + ":" + final_id 
        print(extended_str)
        print(space_str)
        cache.set(str(id), {"ExtendedBrickString":extended_str, "BrickSpace": space_str})
    print('returning', res)
    return res

def extend_id(id, requested_props):
    extended_data = cache.get(id)
    print("Looking up " + id + " and got " + str(extended_data))
    print(requested_props)
    row = {}
    if extended_data:
        for prop in requested_props:
            prop_id = prop["id"]
            print("Checking for " + prop_id)
            if extended_data.get(prop_id): 
                row[prop_id] = [ {"str": extended_data.get(prop_id) }]
            else:
                row[prop_id] = [ {}]
    return row

@app.route("/reconcile", methods=["POST", "GET"])
def reconcile():
    queries = None
    extend_requests = None
    if request.method == "GET":
        queries = json.loads(request.args.get("queries", "[]"))
    else:
        if "extend" in request.form:
            extend_requests = json.loads(request.form.get("extend", "[]"))
        if "queries" in request.form:
            queries = json.loads(request.form.get("queries", "[]"))
    if queries:
        print(queries)
        results = {}
        for qid, q in queries.items():
            results[qid] = {'result': resolve(q)}
        return jsonify(results)
    elif extend_requests:
        print(extend_requests)
        requested_props = extend_requests['properties']
        rows = {}
        meta = [ {"id" : x["id"], "name": x["id"] } for x in requested_props]
        for id in extend_requests["ids"]:
           row = extend_id(id, requested_props)
           rows[id] = row
        results = {}
        # TODO - fix this. check the props actually used?
        results['meta'] = meta
        results['rows'] = rows 
        print(results)
        return jsonify(results)
        
    return jsonify(metadata)

@app.route("/reconcile/properties", methods=["POST", "GET"])
def handle_properties():
    if request.method == "GET":
        if 'type' in request.args:
            type = request.args.get('type')
            props = props_per_type.get(type, [])
            # TODO: I have no idea what a good limit is. Use 5 for now
            return jsonify({"limit": 5, "type": type, "properties": props}) 
    return jsonify({})

if __name__ == "__main__":
    app.run()
