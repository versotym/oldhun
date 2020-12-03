import json
import os
import csv

'''
This script simply stores all the lines in the corpus into single txt file
(emtsv_data/input.txt). This file is then processed by EMTSV. It's output
is parsed back to JSON files.
'''

def parse_emtsv(path):
    ''' 
    Parse output of the EMTSV analysis.
    The output is a list of tokens (including punctuation) where each 
    item has a following structure:
    {
        'token': [string] token as appears in the text
        'morph': [list]   results of morphological analysis parsed from JSON
    }
    :path :  [string] path to a file containing the analysis results 
    '''
    
    # Empty list to store the data
    morph_data = list()

    # Parse tsv file
    with open(path, newline='') as csvfile:
        spamreader = csv.reader(csvfile, delimiter='\t')
        header = True

        # Iterate over rows
        for row in spamreader:
            # If it is a header (first row), skip it
            if header:
                header = False
                continue
            # If it is an empty row (end of sentence marker), skip it
            if not ''.join(row).strip():
                continue
            
            # Add current token and its analysis (JSON) into the list
            morph_data.append({
                'token': row[0],
                'morph': row[4],     #json.loads(row[2]), # <= this loads emTag
                'lemma': row[3],
            });  
            
    return morph_data

if __name__ == '__main__':
      
    lines = list()

    # Create output directory if it don't exist yet
    if not os.path.exists('emtsv_data'):
        os.makedirs('emtsv_data')
    
    # Iterate over JSON files
    for f in sorted(os.listdir('json')):
        print('Storing {} into txt'.format(f))

        # Parse JSON data
        with open(os.path.join('json', f)) as file:
            poem = json.load(file)    
                        
        # Iterate over lines of poem (i-index)
        for i, line in enumerate(poem['body']):
            
            lines.append(line['text'])

    # Store the txt
    l_string = '\n'.join(lines) + '\n\n'
    with open('emtsv_data/input.txt', 'w') as f:
        f.write(l_string)

    # Perform morphological analysis with emtsv
    # TODO: just a temporary workaround - emtsv should be called directly from python
    print('EMTSV running...')
    if os.path.exists("data/output.tsv"):
        os.remove("data/output.tsv")
    path_to_emtsv = 'emtsv'
    os.system('python3 {}/main.py tok,morph,pos -i emtsv_data/input.txt -o emtsv_data/output.tsv'.format(path_to_emtsv))
    
    # Parse data from EMTSV
    morph_data = parse_emtsv('emtsv_data/output.tsv')

    # Current index of the token in parsed EMTSV data
    emtsv_i = 0      
    
    # Iterate over JSON files
    for f in sorted(os.listdir('json')):
        
        print('Parsing {} from tsv'.format(f))

        # Parse JSON data
        with open(os.path.join('json', f)) as file:
            poem = json.load(file)    
                        
        # Iterate over lines of poem
        for i, line in enumerate(poem['body']):
            
            # Iterate over tokens
            for j, token in enumerate(line['tokens']):
                
                # If current token in EMTSV data is a punctuation, skip it
                while (
                    (
                        len(morph_data[emtsv_i]['morph']) > 0 and 
                        morph_data[emtsv_i]['morph'] in (
                            '[Punct]','[Hyph:Dash]','[Hyph:Hyph]','[Hyph:HKJ]'
                        )
                    ) or (
                        morph_data[emtsv_i]['token'] in (
                            '„','”', ',.','’','!.',':)'
                        )
                    )
                ):
                    emtsv_i += 1
                    
                # If current token in the corpus is an ellipsis mark, 
                # assign it empty morph and continue
                if token['token'] in '…':
                    poem['body'][i]['tokens'][j]['morph'] = []
                    continue

                # Raise exception if token in the corpus and token in emtsv differ                    
                if token['token'] != morph_data[emtsv_i]['token']:
                    if ( 
                        token['token'] != '...hat' and 
                        morph_data[emtsv_i]['token'] != 'hat'
                    ):
                        raise Exception(
                            'Tokens mismatch in file {0}[{1}][{2}] ~emtsv[{3}]: {4} != {5}'.format(
                                f, i, j, emtsv_i, token['token'], morph_data[emtsv_i]                   
                            )
                        )

                # Store morph_data into corpus
                poem['body'][i]['tokens'][j]['morph'] = morph_data[emtsv_i]['morph']
                poem['body'][i]['tokens'][j]['lemma'] = morph_data[emtsv_i]['lemma']
                
                # Increase index in parsed EMTSV data
                emtsv_i += 1
            
        # Store poem back to JSON file
        with open(os.path.join('json', f), 'w') as outfile:
            json.dump(poem, outfile, indent=2)
    
    