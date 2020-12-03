import json
import re
import os
from collections import defaultdict
import matplotlib.pyplot as plt
from scipy.stats import pearsonr
import numpy as np
from sklearn.linear_model import LinearRegression
import csv
import math
import numpy as np
import seaborn as sns
import random

'''
This script provides the plots stored in [fig] directory
'''

 
# Custom palette
def palette(no_of_series, index):
    if no_of_series == 1:
        return sns.color_palette("deep", 3)[0]
    else:
        return sns.color_palette("deep", no_of_series)[index-1]
        
    
def get_components(line):
    '''
    Split line into list of vowels and consonant clusters
    '''
    
    # Define vowels
    vowels = 'oeɛøuyiɒaɑɒø'

    # Join transcriptions of words into single string
    ipa = ''.join([x['ipa_espeak'] for x in line['tokens']])

    # Remove garbage
    ipa = re.sub('[ˈˌ\-\.]', '', ipa)

    # Remove length marks
    ipa = re.sub('ː', '', ipa)
    
    # Replace multiple occurrences of a single character in a row
    ipa = re.sub(r'(.)(?=\1)', '', ipa)
    
    # Unify similar vowels
    ipa = re.sub('[eɛ]', 'e', ipa)
    ipa = re.sub('[aɑɒ]', 'a', ipa)    
    
    # Split into components
    ipa = re.sub(r'(['+vowels+'])', r'#\1#', ipa)
    ipa = re.sub(r'(['+vowels+'])#ː', r'\1ː#', ipa)    
    ipa = ipa.split('#')
    return ipa
    

def stanza_sequences_length(stanzas):
    '''
    Count average length of stanza sequences
    '''

    seq_lengths = list()
    current_type = stanzas[0]
    current_length = 1
    for i in range(1, len(stanzas)):                
        if (
            stanzas[i] == stanzas[i-1] and
            stanzas[i] != None
        ):                    
            current_length += 1
            if i == len(stanzas) - 1:
                seq_lengths.append(current_length)
        else:
            seq_lengths.append(current_length)
            current_length = 1
    return np.mean(seq_lengths)    
    

if __name__ == '__main__':
    
    ''' 
    ===========================================================
    Extract data
    =========================================================== 
    '''
    
    # Create output directory if it don't exist yet
    if not os.path.exists('fig'):
        os.makedirs('fig')


    # Data containers    
    counts = defaultdict(lambda: defaultdict(int))
    selected = defaultdict(list)
    stanza_dominants = defaultdict(lambda: defaultdict(list))        
    
    # Iterate over JSON files
    for f in sorted(os.listdir('json')):

        # Print current file name
        print(f)
        
        # Parse JSON data
        with open(os.path.join('json', f)) as file:
            poem = json.load(file)    
    
        # Get metadata and create an abbreviation for the poem
        title = poem['metadata']['title']
        try:
            year = int(poem['metadata']['year'])
        except:
            print('\tnot included: year is not an integer ({})'.format(
                poem['metadata']['year'] 
            ))
            continue
        abbr = str(year) + ' ' + title[:15]
        
        # Add abbreviation to the list if selected author (Bogati|Tinodi)
        if f.startswith('Bogati'):
            selected['Bogati'].append(abbr)
        elif f.startswith('Tinodi'):
            selected['Tinodi'].append(abbr)
            
        #---------------------------------- Stanza sequences

        # Iterate over lines of poem and get v1 | c1v1
        stanzas_v1 = defaultdict(list)
        stanzas_c1v1 = defaultdict(list)
        for i, line in enumerate(poem['body']):
            components = get_components(poem['body'][i])
            stanzas_v1[poem['body'][i]['stanza']].append(components[-2])
            stanzas_c1v1[poem['body'][i]['stanza']].append(''.join(components[-2:]))

        # Get dominant c1|c1v1 in each stanza
        for s in sorted(stanzas_v1):
            dominant = None
            for x in set(stanzas_v1[s]):
                if stanzas_v1[s].count(x) > len(stanzas_v1[s])/2:
                    dominant = x
            stanza_dominants[abbr]['v1'].append(dominant)
            
        #---------------------------------- Rhymed vs. unrhymed lines
        
        # Iterate over lines of poem
        for i, line in enumerate(poem['body']):

            # Count lines 
            counts[abbr]['line-n'] += 1
            # Count lines that do not participate in any rhyme
            if len(line['rhyme']) == 0:
                counts[abbr]['unrhymed-lines'] += 1

        #---------------------------------- Rhyme characteristics

        # Iterate over lines of poem
        for i, line in enumerate(poem['body']):

            # Count lines ending with vala
            if poem['body'][i]['tokens'][-1]['token'] == 'vala':
                counts[abbr]['vala_line'] += 1            

            # Iterate over rhyming lines
            for j in line['rhyme']:
                
                # Skip if it is a preceding line
                # (we don't wanna include rhyme twice)
                if (j < i):
                    continue

                # Increase overall rhyme count
                counts[abbr]['rhyme-n'] += 1
                
                # Split lines into components
                components = (
                    get_components(poem['body'][i]),                
                    get_components(poem['body'][j]),                
                )
                
                # Count identity rhymes
                if j in poem['body'][i]['rhyme_identity']:
                    counts[abbr]['identity'] += 1       
                    
                    if poem['body'][i]['tokens'][-1]['token'] == 'vala':
                        counts[abbr]['vala_rhyme'] += 1
                    
                # Count morphematic rhymes                    
                elif j in poem['body'][i]['rhyme_grammatical']:
                    counts[abbr]['grammatical'] += 1

                    if components[0][-2] != components[1][-2]:
                        counts[abbr]['grammatical_unmatched'] += 1
                    else:
                        counts[abbr]['grammatical_matched'] += 1
                    
                # Count sound matches
                else:
                    if components[0][-1] == components[1][-1]:
                        counts[abbr]['c1'] += 1
                    if components[0][-2] == components[1][-2]:
                        counts[abbr]['v1'] += 1
                    if components[0][-3] == components[1][-3]:
                        counts[abbr]['c2'] += 1
                    if components[0][-4] == components[1][-4]:
                        counts[abbr]['v2'] += 1

    ''' 
    ===========================================================
    Plots
    =========================================================== 
    '''

    print('='*30)

    # Absolute numbers to relative numbers  (rhyme characteristics + unrhymed lines)                                           
    results = defaultdict(list)
    xlabels = list()
    for w in sorted(counts):      
        xlabels.append(w)
        results['identity'].append(counts[w]['identity'] / counts[w]['rhyme-n'])
        results['grammatical'].append(counts[w]['grammatical'] / (counts[w]['rhyme-n'] - counts[w]['identity']))
        results['grammatical_unmatched'].append(counts[w]['grammatical_unmatched'] / (counts[w]['rhyme-n'] - counts[w]['identity']))
        results['grammatical_matched'].append(counts[w]['grammatical_matched'] / (counts[w]['rhyme-n'] - counts[w]['identity']))
        results['c1'].append(counts[w]['c1'] / (counts[w]['rhyme-n'] - counts[w]['identity'] - counts[w]['grammatical']))
        results['c2'].append(counts[w]['c2'] / (counts[w]['rhyme-n'] - counts[w]['identity'] - counts[w]['grammatical']))
        results['v2'].append(counts[w]['v2'] / (counts[w]['rhyme-n'] - counts[w]['identity'] - counts[w]['grammatical']))
        results['unrhymed_lines'].append(counts[w]['unrhymed-lines'] / counts[w]['line-n'])
        results['vala_line'].append(counts[w]['vala_line'] / counts[w]['rhyme-n'])
        results['vala_rhyme'].append(counts[w]['vala_rhyme'] / counts[w]['rhyme-n'])

    # Average length of stanza sequences
    for w in sorted(stanza_dominants):
        for f in stanza_dominants[w]:
            results['stanza_sequences_'+f].append(stanza_sequences_length(stanza_dominants[w][f]))

    # Random model of stanza sequences
    seq_cis = defaultdict(list)
    for w in sorted(stanza_dominants):
        for f in stanza_dominants[w]:
            lengths_random = list()
            for iteration in range(10000):
                stanzas_randomized = random.sample(stanza_dominants[w][f], len(stanza_dominants[w][f]))
                lengths_random.append(stanza_sequences_length(stanzas_randomized))
            results['stanza_sequences_rand_'+f].append(np.mean(lengths_random))
            seq_cis['stanza_sequences_rand_'+f].append(1.96 * np.std(lengths_random, ddof=1))

    # Y-axes labels
    ytitles = {
        'identity': 'frequency of identity rhymes', 
        'grammatical': 'frequency of suffix rhymes',
        'grammatical_unmatched': '',
        'grammatical_matched': '',
        'c1': 'frequency of match',
        'c2': 'frequency of match',
        'v2': 'frequency of match',
        'unrhymed_lines': 'frequency of unrhymed lines',
        'stanza_sequences_v1': 'average sequence length',
        'stanza_sequences_c1v1': 'average sequence length',
        'stanza_sequences_rand_v1': '',
        'stanza_sequences_rand_c1v1': '',
        'vala_line': 'frequency of lines ending with "vala"',
        'vala_rhyme': 'frequency of vala-vala indentity rhymes',
    }

    #---------------------------------- Bar plots
    for m in results:

        # Bar plot
        fig, ax = plt.subplots(figsize=(7,7)) 
        x = range(len(results[m]))
        plt.setp(ax,xticks=range(0,len(xlabels)), xticklabels=xlabels)
        ax.bar(x, results[m], color=palette(1,1))
        ax.tick_params(axis='x', rotation=90)
        ax.set_ylabel(ytitles[m])
        ax.set_xlabel('poem')
        plt.tight_layout()
        plt.savefig(os.path.join('fig', m+'_bar.pdf'))
        plt.close(fig)
        
    #---------------------------------- Scatter plot with highlighted poems
    #---------------------------------- by Tinodi & Bogati
    x1, x2, x3, y1, y2, y3, pointlabels, coords = [],[],[],[],[],[],[],[]
    for xx,yy in zip(xlabels, results['identity']):
        if xx in selected['Bogati']:
            x2.append(int(xx[0:4]))
            y2.append(yy)
            pointlabels.append(xx)
            coords.append((x2[-1], y2[-1]))
        elif xx in selected['Tinodi']:
            x3.append(int(xx[0:4]))
            y3.append(yy)
            pointlabels.append(xx)
            coords.append((x3[-1], y3[-1]))
        else:
            x1.append(int(xx[0:4]))
            y1.append(yy)
    x = [int(l[0:4]) for l in xlabels]

    coef = np.polyfit(x,results['identity'],1)
    poly1d_fn = np.poly1d(coef)     
    r2 = np.corrcoef(x, results['identity'])[0,1] ** 2

    fig, ax = plt.subplots(figsize=(12,12)) 
    ax.scatter(x1, y1, color=palette(3,1))
    ax.scatter(x2, y2, color=palette(3,2), label='Bogáti')
    ax.scatter(x3, y3, color=palette(3,3), label='Tinódi')
    ax.plot(x, poly1d_fn(x), '--k')
    ax.set_ylabel(ytitles['identity'])
    ax.set_xlabel('year of publication')       

    for t,xy in zip(pointlabels, coords):
        if t.startswith('1576'):
            ax.annotate(t,xy, xytext=(xy[0]-10,xy[1]-0.005))
        elif t.startswith('1577'):
            ax.annotate(t,xy, xytext=(xy[0]-8,xy[1]-0))
        elif t.startswith('1579'):
            ax.annotate(t,xy, xytext=(xy[0]-0,xy[1]+0.004))
        elif t.startswith('1587'):
            ax.annotate(t,xy, xytext=(xy[0]-10,xy[1]-0.005))
        elif t.startswith('1598'):
            ax.annotate(t,xy, xytext=(xy[0]-8,xy[1]-0))
        else:           
            ax.annotate(t,xy)
    
    plt.legend()
    plt.savefig(os.path.join('fig', 'identity_selected_scatter.pdf'))
    plt.close(fig)
    
    #---------------------------------- Stacked bar (grammatical rhymes)
    fig, ax = plt.subplots(figsize=(7,7)) 
    x = range(len(results['grammatical']))
    plt.setp(ax,xticks=range(0,len(xlabels)), xticklabels=xlabels)
    ax.bar(x, results['grammatical'], color=palette(2,1), label='all suffix rhymes')
    ax.bar(x, results['grammatical_unmatched'], color=palette(2,2), label='suffix rhymes without phonetic match', width=0.4)
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(ytitles['grammatical'])
    ax.set_xlabel('poem')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join('fig', 'grammatical_stack_bar.pdf'))
    plt.close(fig)

    #---------------------------------- Stacked bar (identity)
    fig, ax = plt.subplots(figsize=(7,7)) 
    x = range(len(results['grammatical']))
    plt.setp(ax,xticks=range(0,len(xlabels)), xticklabels=xlabels)
    ax.bar(x, results['identity'], color=palette(2,1), label='all identity rhymes')
    ax.bar(x, results['vala_rhyme'], color=palette(2,2), label='"vala"-"vala" rhymes', width=0.4)
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(ytitles['identity'])
    ax.set_xlabel('poem')
    plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join('fig', 'identity_stack_bar.pdf'))
    plt.close(fig)
    
    
    #---------------------------------- Stacked bar (sequences)
    macroaverage = np.mean(results['stanza_sequences_v1'])
    fig, ax = plt.subplots(figsize=(7,7)) 
    x = range(len(results['stanza_sequences_v1']))
    plt.setp(ax,xticks=range(0,len(xlabels)), xticklabels=xlabels)
    h1 = ax.bar(x, results['stanza_sequences_v1'], color=palette(2,1), label='observed')
    h2 = ax.bar(x, results['stanza_sequences_rand_v1'], color=palette(2,2), label='expected', width=0.4)
    h3 = ax.errorbar(x, results['stanza_sequences_rand_v1'], yerr=seq_cis['stanza_sequences_rand_v1'], fmt='o', color='black', label='95% confidence interval')
    h4 = ax.hlines(macroaverage, -1,23, label='observed macro-average',linestyles='dotted' )
    ax.tick_params(axis='x', rotation=90)
    ax.set_ylabel(ytitles['stanza_sequences_v1'])
    ax.set_xlabel('poem')
    hh=[h1,h2,h3,h4]
    plt.legend(hh,[H.get_label() for H in hh])
    #plt.legend()
    plt.tight_layout()
    plt.savefig(os.path.join('fig', 'sequences_stack_bar.pdf'))
    plt.close(fig)    
