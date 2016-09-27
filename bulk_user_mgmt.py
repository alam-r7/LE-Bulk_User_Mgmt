import sys
import hashlib, hmac
import base64
import datetime
import requests
import ConfigParser
import csv
import json

#generate Accounts Dictionary
def build_accounts():
    config = ConfigParser.ConfigParser()
    config.read('settings.ini')
    accounts = config.sections()
    accounts_info = {} #values of accounts in a dictionary
    for account in accounts:
        accounts_info[account] = dict(config.items(account))
    return accounts_info

def build_maps(accounts_info, current_account = None):
    existing_users = {}
    response = {}
    amap = {}
    stuff = []
    method = 'GET'
    body = ''
    for account in accounts_info:
        amap[account] = {}
    if current_account == None:
        for account in accounts_info:
            current_account = accounts_info[account]
            uri = 'https://rest.logentries.com/management/accounts/%s/users' % accounts_info[account]['resource-id']
            headers = create_headers(current_account, uri, method, body)
            response = requests.get(uri, headers=headers)
            if response.status_code == 200:
                response = eval(response.text)
                for i in xrange(0, len(response['users'])):
                    existing_users[response['users'][i]['email']] = response['users'][i]['id']
                    amap[account][response['users'][i]['email']] = response['users'][i]['id']
    else:
        uri = 'https://rest.logentries.com/management/accounts/%s/users' % current_account['resource-id']
        headers = create_headers(current_account, uri, method, body)
        response = requests.get(uri, headers=headers)
        if response.status_code == 200:
            response = eval(response.text)
            for i in xrange(0, len(response['users'])):
                existing_users[str(response['users'][i]['email'])] = response['users'][i]['id']
    return existing_users, accounts_info, amap

def gensignature(api_key, date, content_type, request_method, query_path, request_body):
    hashed_body = base64.b64encode(hashlib.sha256(request_body).digest())
    canonical_string = request_method + content_type + date + query_path + hashed_body
    # Create a new hmac digester with the api key as the signing key and sha1 as the algorithm
    digest = hmac.new(api_key, digestmod=hashlib.sha1)
    digest.update(canonical_string)
    return digest.digest()

def create_headers(current_account, uri, method, body):
    date_h = datetime.datetime.utcnow().strftime("%a, %d %b %Y %H:%M:%S GMT")
    content_type_h = "application/json"
    action = uri.split("com/")[1]
    signature = gensignature(current_account['api-key'], date_h, content_type_h, method, action, body)
    headers = {
        "Date": date_h,
        "Content-Type": content_type_h,
        "authorization-api-key": "%s:%s" % (current_account['api-key-id'].encode('utf8'), base64.b64encode(signature))
    }
    return headers

def add_new_users_to_account(current_account, new_users):
    uri = 'https://rest.logentries.com/management/accounts/%s/users' % current_account['resource-id']
    for user in new_users:
        method = 'POST'
        body = {
        "user":
            {
                "email":str(user),
                "first_name":"tmp",
                "last_name":"tmp"
            }
        }
        body = json.dumps(body)
        headers = create_headers(current_account, uri, method, body)
        try:
            response = requests.request('POST', uri, data=body, headers=headers)
            print response.status_code
        except requests.exceptions.RequestException as error:
            print error
        if response.status_code == 201:
            print "new user added: %s" % user

def add_existing_users_to_account(current_account, existing_users, exist_list):
    method = 'POST'
    body = ''
    for user in exist_list:
        key = existing_users[user]
        uri = 'https://rest.logentries.com/management/accounts/%s/users/%s' % (current_account['resource-id'], key)
        headers = create_headers(current_account, uri, method, body)
        try:
            response = requests.request('POST', uri, data='', headers=headers)
        except requests.exceptions.RequestException as error:
            print error
        if response.status_code == 200:
            print "existing user added: %s" % user


def del_missing_users(current_account, existing_users, missing_list):
    method = 'DELETE'
    body = ''
    for user in missing_list:
        key = existing_users[user]
        uri = 'https://rest.logentries.com/management/accounts/%s/users/%s' % (current_account['resource-id'], key)
        headers = create_headers(current_account, uri, method, body)
        try:
            response = requests.request('DELETE', uri, data='', headers=headers)
        except requests.exceptions.RequestException as error:
            print error
        if response.status_code == 204:
            print "deleted user: %s" % user

#Read users file and builds a list of existing users
def get_users_from_csv(existing_users, accounts_info):
    account_map = existing_users
    for u in xrange(1,len(sys.argv)):
        new_list = []
        missing_list = []
        users_exist = []
        text_users = []
        exist_list = []
        users_in_cur_account = []
        in_account = sys.argv[u]
        try:
            filename = str(in_account) + ".txt"
            with open(filename) as file:
                text_users = file.read().splitlines()
        except IOError:
            print 'Error while reading text file: %s' % filename
        try:
            with open("%s_prev_state.txt" % in_account, 'w') as file:
                    for user in text_users:
                        file.write("%s\n" % str(user))
        except IOError:
            print 'Error creating previous state file: %s_prev_state.txt' % in_account
        users_in_cur_account, b, amap = build_maps(accounts_info, current_account = accounts_info[in_account])
        for user in text_users:
            if user in account_map:
                exist_list.append(user)
            if user not in account_map:
                new_list.append(user)
        for user in users_in_cur_account:
            if user not in text_users:
                missing_list.append(user)
        for user in users_in_cur_account:
            if user in exist_list:
                exist_list.remove(user)
        print "user input: %s" % text_users
        print "new users: %s" % new_list
        print "existing users: %s" % exist_list
        print "missing users: %s" % missing_list
        if len(new_list) > 0:
            add_new_users_to_account(accounts_info[in_account], new_list)
        if len(exist_list) > 0:
            add_existing_users_to_account(accounts_info[in_account], existing_users, exist_list)
        if len(missing_list) > 0:
            del_missing_users(accounts_info[in_account], existing_users, missing_list)
        with open("%s_trail.txt" % sys.argv[u], 'a') as file:
            date_h = datetime.datetime.now().strftime("%a, %d %b %Y %H:%M:%S - ")
            if len(new_list) > 0:
                file.write(date_h + "new users added: ")
                for user in new_list:
                    file.write("%s " % str(user))
                file.write("\n")
            if len(exist_list) > 0:
                file.write(date_h + "existing users added: ")
                for user in exist_list:
                    file.write("%s " % str(user))
                file.write("\n")
            if len(missing_list) > 0:
                file.write(date_h + "users deleted: ")
                for user in missing_list:
                    file.write("%s " % str(user))
                file.write("\n")

if __name__ == '__main__':
    if sys.argv[1] != 'build':
        accounts_info = build_accounts()
        existing_users, accounts_info, amap = build_maps(accounts_info, current_account=None)
        get_users_from_csv(existing_users, accounts_info)
    if sys.argv[1] == 'build':
        accounts_info = build_accounts()
        existing_users, accounts_info, amap = build_maps(accounts_info)
        print "this is amap %s" % amap
        for account in accounts_info:
            with open(str(account)+'_map.txt', 'w') as file:
                for user in amap[account]:    
                    file.write(user+'\n')