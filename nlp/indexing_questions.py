# Transform question-vectorisation from postgresql to elastic search

import json
import time

from elasticsearch import Elasticsearch
import psycopg2
import psycopg2.extras
import uuid



es = Elasticsearch()


def main():
    # delete the old index in case it already exists
    es.indices.delete(index='qa', ignore=[400, 404])
    # and create a new one
    with open('./nlp/index.json') as index_file:
        source = index_file.read().strip()
        es.indices.create(index='qa', body=source)

    # connect to database
    f = open('db-credentials/config.json') # load config file
    dbconfig = json.load(f) # load credentials details
    conn = psycopg2.connect("dbname=%s user=%s host=%s port=%d password=%s"
        % (dbconfig['database'], dbconfig['user'], dbconfig['host'], dbconfig['port'], dbconfig['password']))
    cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor) # use psycopg2.extras.DictCursor to return row as dict object

    # retrieve all questions
    cur.execute("SELECT * FROM question where question_valid=1;")
    q = cur.fetchone()
    cnt = 0
    while q:
        doc = {
            'id': q['id'],
            'text': q['question_text'],
            'vectorisation': q['vectorisation'],
            'rep': q['question_tsv']
        }
        es.index(index='qa', body=doc, id=q['id'])
        cnt += 1
        print('done for %d - processed: %d' % (q['id'], cnt))
        q = cur.fetchone()
    # close the database
    cur.close()
    conn.close()


def verify():
    doc = {
        'size' : 10000,
        'query': {
            'match_all' : {}
        }
    }
    res = es.search(index='qa', body=doc)
    print(res['hits']['total'])
    #print(es.get(index='qa', doc_type='questions', id=2301))


if __name__ == '__main__':
    main()
    time.sleep(1) # elastic search refreshes every 1s, u need to sleep a bit to be able to see new index docs
    verify()