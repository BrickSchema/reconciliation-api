from flask import Flask, request
from flask_jsonpify import jsonify
from abbrmap import abbrmap as tagmap
import json
import brickschema
import re

app = Flask(__name__)

metadata = {
    "name": "Brick Reconciliation Service",
    "defaultTypes": [
        {"id": "EquipmentClass", "name": "EquipmentClass"},
        {"id": "PointClass", "name": "PointClass"}
    ]
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
    brick_tags = flatten([tagmap.get(tag.lower(), [tag]) for tag in tags])

    if q.get('type') == 'PointClass':
        brick_tags += ['Point']
    elif q.get('type') == 'EquipmentClass':
        brick_tags += ['Equipment']

    res = []
    most_likely, leftover = inf.most_likely_tagsets(brick_tags, limit)
    for ml in most_likely:
        res.append({
            'id': q['query'],
            'name': ml,
            'score': (len(brick_tags) - len(leftover)) / len(brick_tags),
            'match': len(leftover) == 0,
            'type': [{"id": "PointClass", "name": "PointClass"}],
        })
    print('returning', res)
    return res


@app.route("/reconcile", methods=["POST", "GET"])
def reconcile():
    if request.method == "GET":
        queries = json.loads(request.args.get("queries", "[]"))
    else:
        queries = json.loads(request.form.get("queries", "[]"))
    print(queries)
    if queries:
        results = {}
        for qid, q in queries.items():
            results[qid] = {'result': resolve(q)}
        return jsonify(results)
    return jsonify(metadata)


if __name__ == "__main__":
    app.run(debug=True)
