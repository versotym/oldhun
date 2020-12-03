import json
import re
import os
import requests

'''
This script performs rhyme detection.
Data are parsed from JSON files stored in [JSON] directory, enriched
and dumped back to JSON files.
'''

def remove_existing_rhymes(poem):
    '''
    Remove rhymes from previous tagging
    '''

    for i, line in enumerate(poem['body']):
        poem['body'][i]['rhyme'] = []
        poem['body'][i]['rhyme_identity'] = []
        poem['body'][i]['rhyme_v_match'] = []
        poem['body'][i]['rhyme_grammatical'] = []
        
    return poem


def line_final_vowel(line):
    '''
    Extract line-final vowel
    '''    
    
    vowels = 'oeɛøuyiɒaɑɒø'
    fin_word = line['tokens'][-1]['ipa_espeak']
    fin_vowel = re.sub('[^' + vowels + ']', '', fin_word)[-1]

    return similar_vowels(fin_vowel)


def similar_vowels(vowel):
    '''
    Merge similar vowels under single representation
    '''
    
    vowel = re.sub('[eɛ]', 'e', vowel)
    vowel = re.sub('[aɑɒ]', 'a', vowel)
    
    return vowel
    
    
def line_final_morphemes(line):
    '''
    Extract line final morphemes
    '''
    
    # Extract last words morphemes (possible multiple interpretations => list)
    morph = line['tokens'][-1]['morph']
    
    # Count number of morphemes and extract line final morpheme
    #morph = re.sub('\[ *\]$', '', morph)
    n = morph.count('[')
    morph =  re.sub(r'^.*(\[[^\]]+\])$', r'\1', morph)
    
    return re.sub('[\[\]]', '', morph), n

if __name__ == '__main__':  

    # Iterate over JSON files
    for f in sorted(os.listdir('json')):

        # Print current file name
        print('\n\t', f)
        
        # Parse JSON data
        with open(os.path.join('json', f)) as file:
            poem = json.load(file)    
            
        # Remove rhymes from previous taggings / 
        # create an empty 'rhyme' list in each line
        poem = remove_existing_rhymes(poem)
                        
        # Iterate over lines of poem (i-index)
        for i, line in enumerate(poem['body']):
                                                   
            # Extract line final vowel and final morpheme from i-line
            fin_vowel1 = line_final_vowel(poem['body'][i])
            morph1,l1 = line_final_morphemes(poem['body'][i])

            # Iterate over lines that follows the one in question (j-index)         
            for j in range(i+1, len(poem['body'])):

                # Stop the loop if j-index is outside the i-line's stanza
                if poem['body'][i]['stanza'] != poem['body'][j]['stanza']:
                    break

                # Extract line final vowel  and final morpheme from j-line
                fin_vowel2 = line_final_vowel(poem['body'][j])
                morph2,l2 = line_final_morphemes(poem['body'][j])
                
                # If neither line-final vowels match, nor morphemes match
                # => continue (it's not a rhyme)
                if (
                    fin_vowel1 != fin_vowel2 and
                    ( morph1 != morph2 or morph1 == 'Nom' )
                ):
                    continue
                
                # Store rhyme and its characteristics
                poem['body'][i]['rhyme'].append(j)
                poem['body'][j]['rhyme'].append(i)
                
                if fin_vowel1 == fin_vowel2:
                    poem['body'][i]['rhyme_v_match'].append(j)
                    poem['body'][j]['rhyme_v_match'].append(i)
                if poem['body'][i]['tokens'][-1]['token'].lower() == poem['body'][j]['tokens'][-1]['token'].lower():
                    poem['body'][i]['rhyme_identity'].append(j)
                    poem['body'][j]['rhyme_identity'].append(i)
                if morph1 == morph2 and morph1 != 'Nom': # and l1 > 1:
                    poem['body'][i]['rhyme_grammatical'].append(j)
                    poem['body'][j]['rhyme_grammatical'].append(i)
                                                
        # Store poem back to JSON file
        with open(os.path.join('json', f), 'w') as outfile:
            json.dump(poem, outfile, indent=2)