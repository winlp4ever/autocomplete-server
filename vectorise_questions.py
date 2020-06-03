import psycopg2
import json
from tokenizer import Token

tk = Token()
from sentence_transformers import SentenceTransformer
mod = SentenceTransformer('distiluse-base-multilingual-cased')


# read db-config file
f = open('db-credentials/config.json')

dbconfig = json.load(f)
# connect to the server
conn = psycopg2.connect("dbname=%s user=%s host=%s port=%d password=%s"
    % (dbconfig['database'], dbconfig['user'], dbconfig['host'], dbconfig['port'], dbconfig['password']))

cur = conn.cursor()

# extract all questions from the table 'question'
cur.execute("SELECT id, question_text FROM question;")
questions = cur.fetchall()

# iterate over all questions
processed = 0
total = 0
for idx, text in questions:
    tks = tk.tokenize([text])[0]
    embeddings = mod.encode([tks])[0].tolist()
    cur.execute("update question set dimensions=%s, vectorisation=%s where id=%s", [len(embeddings), embeddings, idx])
    print('done for question with %d - total processed questions: %d' % (idx, processed))
    processed += 1

conn.commit()

# close the database
cur.close()
conn.close()