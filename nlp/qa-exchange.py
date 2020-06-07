import json
from time import sleep
import socketio
from collections import deque
from similarity_search import SimiSearch 
import psycopg2
import psycopg2.extras
import random

import json
import time 
from datetime import datetime
import requests

import asyncio

from functools import lru_cache

sio = socketio.AsyncClient(ssl_verify=False)
print('1')
questions_queue = deque()
hints_queue = deque()
bob = {
    'username': 'bob',
    'email': '',
    'userid': -1
}
template = {
    'user': bob,
    'type': 'chat',
    'text': '',
}

sim = SimiSearch()

@lru_cache(maxsize=50000)
def simQuestions(s):
    '''
    Combine elasticsearch with python lru-cache to improve performance
    '''
    if len(s) <= 2:
        return []
    return sim.findSimQuestions(s, 5)

print('2')
from psycopg2 import pool


# load db credentials
f = open('db-credentials/config.json')
dbconfig = json.load(f)
f.close()

conversations = {}

async def run():
    try:
        postgreSQL_pool = psycopg2.pool.SimpleConnectionPool(1, 2000, host=dbconfig['host'], database=dbconfig['database'],
            user=dbconfig['user'], password=dbconfig['password'], port=dbconfig['port'],
            connect_timeout=2)
        if (postgreSQL_pool):
            print("Connection pool created successfully")

        ps_connection  = postgreSQL_pool.getconn()

        if(ps_connection):
            print("successfully received connection from connection pool ")

        # load azure credentials
        f = open('azure-credentials/config.json')
        azureConfig = json.load(f)
        f.close()

        @sio.event
        def connect():
            print('connection established')

        @sio.on('ask-bob')
        async def on_message(msg):
            await sio.emit('bob-msg', get_answer(msg))

        @sio.on('ask-for-hints-bob')
        async def on_message(msg):
            await sio.emit('bob-hints', get_hints(msg))

        @sio.event
        def disconnect():
            print('disconnected from server')

        def getRelatedQuestions(id):
            cur = ps_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
            cur.execute(''' 
                select question_relations.id_target as trg, question.question_text
                from 
                    (
                        select distinct question_id 
                        from 
                            question_answer_temp
                    ) as qs
                inner join 
                    question_relations
                on question_relations.id_target = qs.question_id 
                inner join 
                    question 
                on qs.question_id = question.id
                where question_relations.id_origin=%s
            ''', [str(id)])
            res = cur.fetchall()
            cur.close()
            return res


        def get_answer(old_msg):
            question = old_msg['chat']['text']
            global sim
            qs = simQuestions(question)
            print(qs)

            msg = template.copy()
            msg['original_question'] = question
            tm = datetime.fromtimestamp(time.time())
            msg['datetime'] = '{}/{}/{} {}:{}:{}'.format(tm.day, tm.month, tm.year, tm.hour, tm.minute, tm.second)
            sol_id = -1

            if qs and qs[0]['score'] > 0.95:
                print(qs[0]['id'])
                cur = ps_connection.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

                if not qs[0]['rep']:
                    # question type mon code ne marche pas
                    cur.execute('''
                        select * from activities 
                        where activitytype = 'submit' 
                        and status = false 
                        and exerciseid = %d
                        and studentid = %d
                        order by id desc, date desc
                    ''' % (old_msg['chat']['user']['exerciseid'], old_msg['conversationID']))
                    res = cur.fetchone()
                    if res:
                        msg['answer'] = res['record']
                        msg['text'] = res['record']['message']
                        msg['type'] = 'exercise-err-message'
                        msg['original_question'] = question
                    else:
                        cur.execute('''
                            select error_code_message, error_code_count
                            from error_codes
                            where id_exercise = %d
                            order by error_code_count desc
                        ''' % old_msg['chat']['user']['exerciseid'])
                        res = cur.fetchall()
                        msg['answer'] = res[:4] if res else []
                        msg['type'] = 'exercise-common-errs'
                        msg['original_question'] = question
                    cur.close()
                    return {
                        'chat': msg,
                        'conversationID': old_msg['conversationID']
                    }
                cur.execute('''
                    select answer_temp.*, q.*
                    from 
                        question_answer_temp
                    inner join
                        (
                            select qs.id as qid, question.question_fuzzy as fuzzy
                            from 
                                question 
                            inner join
                                question as qs
                            on (
                                    question.id = qs.question_equivalent 
                                    or question.id = qs.id 
                                    or question.question_equivalent = qs.id
                                    or (
                                            question.question_equivalent = qs.question_equivalent 
                                            and question.question_equivalent > 0
                                        )
                                ) 
                            where question.id = %s
                        ) as q
                    on (q.qid = question_answer_temp.question_id)
                    inner join 
                        answer_temp
                    on question_answer_temp.answer_temp_id = answer_temp.id
                    where answer_temp.answer_valid = '1' 
                    order by answer_temp.answer_teacher_manual_review desc, answer_rank, answer_temp.id asc;
                ''', [str(qs[0]['id'])])
                ans = cur.fetchone()
                if ans:
                    res = ans.copy()        
                    while ans:
                        if ans['answer_level'] == old_msg['chat']['user']['level']:
                            res = ans
                            break
                        ans = cur.fetchone()
                    msg['answer'] = res
                    msg['text'] = res['answer_paragraph'][:90]
                    sol_id = res['qid']
                    if len(res['answer_paragraph']) > 90 and not msg['text'].endswith('..'):
                        msg['text'] += '...'
                
                # close the database
                cur.close()                
            
            print('responded.')
            msg['related_questions'] = getRelatedQuestions(sol_id)
            #msg['related_questions'] = []
            msg['type'] = 'answer'
            return {
                'chat': msg,
                'conversationID': old_msg['conversationID']
            }


        def get_hints(msg):
            question = msg['typing']
            global sim
            global conversations
            convID = msg['conversationID']
            if convID not in conversations:
                conversations[convID] = msg['timestamp']
            else:
                if msg['timestamp'] < conversations[convID]:
                    return {
                        'hints': [],
                        'conversationID': msg['conversationID'],
                        'timestamp': msg['timestamp'],
                        'socketid': msg['socketid']
                    }
                conversations[convID] = msg['timestamp']
            try:
                st = time.time()
                qs = simQuestions(question)
                print('search-time : %f' % (time.time()-st))
            except Exception as e:
                print(e)
                qs = []
            return {
                'hints': qs,
                'conversationID': msg['conversationID'],
                'timestamp': msg['timestamp'],
                'socketid': msg['socketid']
            }

        await sio.connect('https://localhost:5000')
        await sio.wait()
    except (Exception, psycopg2.DatabaseError) as error :
        print (error)

    finally:
        if (postgreSQL_pool):
            postgreSQL_pool.closeall
        print("PostgreSQL connection pool is closed")


#asyncio.run(run())
loop = asyncio.get_event_loop()
loop.run_until_complete(run())
