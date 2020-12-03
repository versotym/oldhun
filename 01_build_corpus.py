import os
import re
import epitran
from subprocess import check_output
import quntoken
import json

'''
This script iterates over txt files stored in [src] directory and

(1) loads the texts and their metadata,
(2) performs tokenization and phonetic transcription
(3) stores the results in json into [json] directory.

The structure of output is as follows:

{
    'file':                [string] filename of the original txt file
    'metadata': {
        'author':          [string] author of the poem,
        'title':           [string] title of the poem,
        'year':            [string] year when poem published,
        'imm':             [list] indication of melodic model,
    },
    'body':     [{
        'text':            [string] text_of_line,
        'punct_init':      [string] potential line-initial punctuation,
        'stanza':          [int] id_of_stanza,
        'tokens': [{
            'token':       [string] word-token, 
            'ipa_espeak':  [string] ipa produced by espeak,
            'ipa_epitran': [string] ipa produce by epitran,
            'punct':       [string] potential punctuation following the token,
         } ... ],
    } ... ],
}
'''


def tokenize(text):
    '''
    Tokenize the text by means of QUNTOKEN. Output is the list structured as
    [{'token': word-token, 'punct': potential punctuation following the word}] 
    and string punct_init holding potential line-initial punctuation mark
    '''

    # Regex formula to check whether token is a punctuation mark
    punct_regex = '^[\–\.\(\)\„\”\’\!\[\]\:\?\;\-\,]*$'

    # Output variables
    tokens = []
    punct_init = None

    # Iterate over tokens
    for t in quntoken.tokenize(text):

        # Get rid of word-boundary chars
        t = t.split('\t')[0]

        # If token is a punctuation mark...
        if re.search(punct_regex, t):
 
            # if it is line-initial char, store it into punct_init
            if len(tokens) == 0:
                punct_init = t

            # otherwise store it to the last element in output list
            else:
                tokens[-1]['punct'] = t

        # If token is not a punctuation, append new entry into output list
        else:
            tokens.append({'token': t, 'punct': None})

    return tokens, punct_init


def _ipa_epitran(text):
    '''
    Transcribe text to IPA by means of EPITRAN
    '''

    epi = epitran.Epitran('hun-Latn')
    ipa = epi.transliterate(text)
    ipa = ipa.replace('\n', ' ')
    ipa = re.sub(' +', ' ', ipa)
    return ipa


def _ipa_espeak(text):
    '''
    Transcribe text to IPA by means of ESPEAK
    '''

    text = re.sub('^\-', '', text)
    ipa = check_output(["espeak", "-q", "--ipa", '-v', 'hu-hu', text]).decode('utf-8')
    ipa = ipa.replace('\n', ' ')
    ipa = re.sub(' +', '', ipa)
    return ipa


def process_file(path):
    '''
    Load poem from file into an object with following structure:
    [{
        'text':            [string] text_of_line,
        'punct_init':      [string] potential line-initial punctuation,
        'stanza':          [int] id_of_stanza,
        'tokens': [{
            'token':       [string] word-token, 
            'ipa_espeak':  [string] ipa produced by espeak,
            'ipa_epitran': [string] ipa produce by epitran,
            'punct':       [string] potential punctuation following the token,
         } ... ],
    } ... ]
    :: path  = path to a file (str)
    '''
    
    # Red content of the file
    file = open(path, "r")
    content = file.read().splitlines()

    # Output variable where data on poem will be stored
    poem = list()
    # Dict to store metadata
    metadata = dict()
    # Index of the stanza
    stanza_id = 1

    # Iterate over lines of text
    for i,c in enumerate(content):
        
        # Print current line index
        print(i+1, end=' ', flush=True)

        # If it is part of metadata (first 4 lines), 
        # store it as metadata and continue
        if i <= 3:
            key, content = c.split(':', 1)
            key = key.strip()
            content = content.strip()
            if key == 'imm':
                content = content.split(',')
                content = [x.strip() for x in content]
            elif content == '':
                content = None
            metadata[key] = content
            continue

        # If line empty, increase the stanza index and continue
        if c.strip() == '':
            if len(poem) > 0:
                stanza_id += 1
            continue

        # Tokenize the line        
        tokens, punct_init = tokenize(c)
        
        # Iterate over tokens and get phonetic transcription
        for j,t in enumerate(tokens):
            tokens[j]['ipa_epitran'] = _ipa_epitran(t['token'])
            tokens[j]['ipa_espeak'] = _ipa_espeak(t['token'])
            
        # Append data to the output                
        poem.append({
            'text': c, 
            'tokens': tokens,
            'punct_init': punct_init,
            'stanza': stanza_id})
        
    return poem, metadata    


if __name__ == '__main__':

    # Create output directory if it don't exist yet
    if not os.path.exists('json'):
        os.makedirs('json')

    # Iterate over TXT files
    for f in sorted(os.listdir('src')):

        # Skip if file already processed
        if os.path.isfile(os.path.join('json', f.replace('.txt', '.json'))):
            continue
        
        # Print current file name
        print('\n\t', f)

        # Read file conent, tokenize and perform phonetic transcription
        poem, metadata = process_file(os.path.join("src", f))

        # Append poem and metadata to the list
        data = {'metadata': metadata, 'file': f, 'body': poem}
        
        # Store data to json file
        with open(os.path.join('json', f.replace('.txt', '.json')), 'w') as outfile:
            json.dump(data, outfile, indent=2)
