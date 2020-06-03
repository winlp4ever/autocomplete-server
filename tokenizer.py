#!/usr/bin/python3

import sys
from nltk.tokenize.stanford import StanfordTokenizer
import re
import os

SNLP_TAGGER_JAR = "/home/redlcamille/workspace/bob/nlp/stanford-postagger.jar"


def tokenize(tknzr, sentence, to_lower=True):
    """Arguments:
        - tknzr: a tokenizer implementing the NLTK tokenizer interface
        - sentence: a string to be tokenized
        - to_lower: lowercasing or not
    """
    sentence = sentence.strip()
    sentence = ' '.join([format_token(x) for x in tknzr.tokenize(sentence)])
    if to_lower:
        sentence = sentence.lower()
    sentence = re.sub('((www\.[^\s]+)|(https?://[^\s]+)|(http?://[^\s]+))','<url>',sentence) #replace urls by <url>
    sentence = re.sub('(\@ [^\s]+)','<user>',sentence) #replace @user268 by <user>
    filter(lambda word: ' ' not in word, sentence)
    return sentence

def format_token(token):
    """"""
    if token == '-LRB-':
        token = '('
    elif token == '-RRB-':
        token = ')'
    elif token == '-RSB-':
        token = ']'
    elif token == '-LSB-':
        token = '['
    elif token == '-LCB-':
        token = '{'
    elif token == '-RCB-':
        token = '}'
    return token

def tokenize_sentences(tknzr, sentences, to_lower=True):
    """Arguments:
        - tknzr: a tokenizer implementing the NLTK tokenizer interface
        - sentences: a list of sentences
        - to_lower: lowercasing or not
    """
    return [tokenize(tknzr, s, to_lower) for s in sentences]


class Token:
    def __init__(self):
        self.tk = StanfordTokenizer(SNLP_TAGGER_JAR, encoding='utf-8')
    
    def tokenize(self, sentences):
        s = ' <delimiter> '.join(sentences)
        tokenized_sentences_SNLP = tokenize_sentences(self.tk, [s])
        return tokenized_sentences_SNLP[0].split(' <delimiter> ')
    

if __name__ == '__main__':
    s = sys.argv[1]
    sentences = [s]
    
    print('sentences: \n {}'.format(sentences))
    tk = Token()

    print(tk.tokenize(sentences))
