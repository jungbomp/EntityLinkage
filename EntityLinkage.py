import requests
from urllib.parse import quote
from nltk.metrics import distance
from nltk import ngrams
import xml.etree.ElementTree as ET
import csv


def dblp_author_api_query(query_term, format):
    DBLP_AUTHOR_API_URL = 'https://dblp.org/search/author/api'

    query_str = '{0}?q={1}&format={2}&h=1000&c=1000'.format(DBLP_AUTHOR_API_URL, quote(query_term), quote(format))
    resp = requests.get(query_str)
    if resp.status_code != 200:
        # This means something went wrong.
        raise ApiError('GET /tasks/ {}'.format(resp.status_code))

    ret = []
    entities = resp.json()['result']['hits'];
    if 0 < int(entities['@sent']):
        for entity in entities['hit']:
            ret.append(entity['info'])

    print('Query to DBLP Author API with {0} and retrived {1} ressults'.format(query_term, len(ret)))
    
    return ret


def dbpedia_keyword_search_api_query(query_term, type):
    DBPEDIA_KEYWORD_SEARCH_API_URL = 'http://lookup.dbpedia.org/api/search.asmx/KeywordSearch'

    if type.lower() == 'organization':
        type = 'Organisation'

    query_str = '{0}?QueryClass={1}&QueryString={2}'.format(DBPEDIA_KEYWORD_SEARCH_API_URL, quote(type), quote(query_term))
    resp = requests.get(query_str)
    if resp.status_code != 200:
        # This means something went wrong.
        raise ApiError('GET /tasks/ {}'.format(resp.status_code))

    ret = []
    root = ET.fromstring(resp.content)
    ns = {'xmlns': 'http://lookup.dbpedia.org/'}
    for result in root.findall('xmlns:Result', ns):
        print(result.find('xmlns:Label', ns).text, result.find('xmlns:URI', ns).text)
        ret.append({'Label':result.find('xmlns:Label', ns).text, 'URI': result.find('xmlns:URI', ns).text})

    print('Query to DBPEDIA keyword search API with {0} and retrived {1} ressults'.format(query_term, len(ret)))
    
    return ret


def run_jaro_winkler_similarity(lhs, entities):
    max_similarity = [('', '', 0.0),]

    for entity in entities:
        similarity = distance.jaro_winkler_similarity(lhs, entity['author'])
        if max_similarity[0][2] < similarity:
            max_similarity = [(entity['author'], entity['url'], similarity),]
        elif max_similarity[0][2] == similarity:
            max_similarity.append((entity['author'], entity['url'], similarity))

    print('Jaro Winkler similarity with {0} and {1} entities results in {2} miximum similarity of {3}'.format(lhs, len(entities), len(max_similarity), max_similarity[0][2]))

    return max_similarity


def run_jaro_similarity(lhs, entities):
    max_similarity = [('', '', 0.0),]

    for entity in entities:
        similarity = distance.jaro_similarity(lhs, entity['author'])
        if max_similarity[0][2] < similarity:
            max_similarity = [(entity['author'], entity['url'], similarity),]
        elif max_similarity[0][2] == similarity:
            max_similarity.append((entity['author'], entity['url'], similarity))

    print('Jaro similarity with {0} and {1} entities results in {2} miximum similarity of {3}'.format(lhs, len(entities), len(max_similarity), max_similarity[0][2]))

    return max_similarity


def jaccard_distance_similarity(lhs, entities):
    min_similarity = [('', '', 1000000.0),]

    for entity in entities:
        similarity = distance.jaccard_distance(set(ngrams(lhs, n=2)), set(ngrams(entity['author'], n=2)))
        if similarity < min_similarity[0][2]:
            min_similarity = [(entity['author'], entity['url'], similarity),]
        elif min_similarity[0][2] == similarity:
            min_similarity.append((entity['author'], entity['url'], similarity))

    print('Jaccard distance with {0} and {1} entities results in {2} minimum similarity of {3}'.format(lhs, len(entities), len(min_similarity), min_similarity[0][2]))

    return min_similarity


if __name__ == '__main__':

    ret_format = 'json'
    ret = []

    with open('input.csv') as in_file:
        csv_reader = csv.reader(in_file, delimiter=',')
        
        for row in csv_reader:
            if row[1] != 'Person':
                continue
            
            similarity = [('', '', 0.0),]            
            entities = dblp_author_api_query(row[2], ret_format)
            if 0 < len(entities):
                similarity = jaccard_distance_similarity(row[2], entities)
                
            if 1 < len(similarity):
                entities = list(map(lambda x : {'author': x[0], 'url': x[1]}, similarity))
                similarity = run_jaro_winkler_similarity(row[2], entities)
            
            if 1 < len(similarity):
                entities = list(map(lambda x : {'author': x[0], 'url': x[1]}, similarity))
                similarity = run_jaro_similarity(row[2], entities)
            
            for tp in similarity:
                ret.append([row[1], row[2], tp[0], tp[1], tp[2]])

    with open('output.csv', mode='w') as out_file:
        csv_writer = csv.writer(out_file, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in ret:
            csv_writer.writerow(row)
