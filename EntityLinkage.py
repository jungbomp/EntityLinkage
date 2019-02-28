import requests
from urllib.parse import quote
from nltk.metrics import distance
import xml.etree.ElementTree as ET
import csv


def dblp_author_api_query(query_term, format):
    DBLP_AUTHOR_API_URL = 'https://dblp.org/search/author/api'

    query_str = '{0}?q={1}&format={2}'.format(DBLP_AUTHOR_API_URL, quote(query_term), quote(format))
    resp = requests.get(query_str)
    if resp.status_code != 200:
        # This means something went wrong.
        raise ApiError('GET /tasks/ {}'.format(resp.status_code))

    ret = []
    entities = resp.json()['result']['hits'];
    if 0 < int(entities['@sent']):
        for entity in entities['hit']:
            ret.append(entity['info'])
    
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
    
    # entities = resp.json()['result']['hits'];
    # if 0 < int(entities['@sent']):
    #     for entity in entities['hit']:
    #         ret.append(entity['info'])
    
    return ret


if __name__ == '__main__':

    ret_format = 'json'

    task_1 = []
    task_2 = []

    with open('input.csv') as in_file:
        csv_reader = csv.reader(in_file, delimiter=',')

        
        for row in csv_reader:
            if row[1] == 'Person':            
                entities = dblp_author_api_query(row[2], ret_format)
                max_similarity = [('', '', 0.0),]
                
                for entity in entities:
                    similarity = distance.jaro_winkler_similarity(row[2], entity['author'])
                    if max_similarity[0][2] < similarity:
                        max_similarity = [(entity['author'], entity['url'], similarity),]
                    elif max_similarity[0][2] == similarity:
                        max_similarity.append((entity['author'], entity['url'], similarity))

                for tp in max_similarity:
                    task_1.append([row[1], row[2], tp[0], tp[1], tp[2]])

            elif row[1] in ['Organization', 'Company']:
                entities = dbpedia_keyword_search_api_query(row[2], row[1])
                max_similarity = [('', '', 0.0),]

                for entity in entities:
                    similarity = distance.jaro_winkler_similarity(row[2], entity['Label'])
                    if max_similarity[0][2] < similarity:
                        max_similarity = [(entity['Label'], entity['URI'], similarity),]
                    elif max_similarity[0][2] == similarity:
                        max_similarity.append((entity['Label'], entity['URI'], similarity))

                for tp in max_similarity:
                    task_2.append([row[1], row[2], tp[0], tp[1], tp[2]])

    with open('task1_csv', mode='w') as out_file1:
        csv_writer = csv.writer(out_file1, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in task_1:
            csv_writer.writerow(row)

    with open('task2_csv', mode='w') as out_file2:
        csv_writer = csv.writer(out_file2, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)
        for row in task_2:
            csv_writer.writerow(row)