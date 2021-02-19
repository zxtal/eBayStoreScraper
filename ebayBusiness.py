import requests
from lxml import etree
from pandas import DataFrame
import re


url = 'https://www.ebay.com/sns'
headers = {'User-Agent':'Mozilla/5.0 (Macintosh; Intel Mac OS X 10_13_6) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/80.0.3987.149 Safari/537.36'}
search_term = input('Please enter a keyword here: ')


store_data = {
            'business_url': [],
            'business_name': [],
            'business_description': [],
            'user_name': [],
            'feedback_score': [],
            'number_of_items': [],
            'followers': [],
            'user_since': [],
            'location': []
    }

def page_num_generator():
    page = 1
    while True:
        yield page
        page += 1


pages_gen = page_num_generator()

has_next_page = True
while has_next_page:
    page_number = next(pages_gen)
    params = {'store_search': search_term, '_pgn': page_number}
    response = requests.get(url=url, params=params)
    page_text = response.text
    tree = etree.HTML(page_text)
    store_list = tree.xpath("//div[@id='mainContent']//ul[@class='sns-items']/li")

    if not store_list:
        has_next_page = False

    for li in store_list:
        ## 1.business store url added
        link = li.xpath("./div/a/@href")[0]

        ## 2.business name added
        business_name = li.xpath("./div/a/text()")[0]

        ## 3.description added
        description = li.xpath("./div[2]/text()")
        if len(description) != 0:
            business_description = description[0]
        else:
            business_description = 'none'

        store_page_text = requests.get(url=link, headers=headers).text
        tree = etree.HTML(store_page_text)
        number_items_for_sale_tag = tree.xpath("//h2[@class='srp-controls__count-heading']/text()")
        if number_items_for_sale_tag:
            number_items_for_sale = re.findall(r'of (.+) Results', number_items_for_sale_tag[0])[0]
        else:
            number_items_for_sale = 'na'

        user_link_tag = tree.xpath("//div[@class='str-metadata']/span[@class='str-metadata__seller-link']/a/@href")
        if user_link_tag:
            user_link = user_link_tag[0]
        elif tree.xpath("//div[@class='mbg']/a/@href"):
            user_link = tree.xpath("//div[@class='mbg']/a/@href")[0]
        else:
            continue

        # store retrieved data in respective lists
        store_data['business_url'].append(link)
        store_data['business_name'].append(business_name)
        store_data['business_description'].append(business_description)

        user_page_text = requests.get(url=user_link, headers=headers).text
        tree = etree.HTML(user_page_text)

        ## 4.user name added
        user_name = tree.xpath("//div[@class='mbg']//a[@class='mbg-id']/text()")[0]
        store_data['user_name'].append(user_name)

        ## 5.feedback score added
        feedback_score_tag = tree.xpath("//div[@class='mbg']//a[2]/text()")
        if feedback_score_tag:
            feedback_score = feedback_score_tag[0]
        else:
            feedback_score = '0'
        store_data['feedback_score'].append(feedback_score)

        ## 6.number of items added
        number_items_for_sale_tag1 = tree.xpath("//span[@class='sell_count']/a/text()")
        if number_items_for_sale_tag1:
            number_items_for_sale = number_items_for_sale_tag1[0]
        store_data['number_of_items'].append(number_items_for_sale)

        ## 7.followers added
        followers_tag = tree.xpath("//div[@id='member_info']/span[1]/span/@contentstring")[0]
        followers = re.findall(r'>(.+)</', followers_tag)[0]
        store_data['followers'].append(followers)

        ## 8.user since date added
        user_since = tree.xpath("//div[@id='member_info']/span[5]/span[@class='info']/text()")[0]
        store_data['user_since'].append(user_since)

        location = tree.xpath("//div[@id='member_info']/span[8]/text()")[0]
        ## 9.location added
        store_data['location'].append(location)
        print(page_number,' ', link, ' ', user_name)
        print(store_data)
    page_number += 1



##storing data into DataFrame
df = DataFrame(data=store_data)
df.drop_duplicates(subset='business url', keep='first', inplace=True)
df.to_csv(f'./{search_term}.csv')
print(f'Scraping for {search_term} done!')
