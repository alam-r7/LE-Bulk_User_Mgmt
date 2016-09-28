import sys
import hashlib, hmac
import base64
import datetime
import requests
import ConfigParser
import json

def build_accounts():
    config = ConfigParser.ConfigParser()
    config.read('settings.ini')
    accounts = config.sections()
    accounts_info = {}
    for account in accounts:
        accounts_info[account] = dict(config.items(account))
    return accounts_info

def build_maps(accounts_info, current_account = None):
    existing_users = {}
    response = {}
    amap = {}
    for account in accounts_info:
        amap[account] = {}
    method = 'GET'
    body = ''
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
        uri = 'https://rest.logentries.com/management/accounts/%s/users' % accounts_info[current_account]['resource-id']
        headers = create_headers(accounts_info[current_account], uri, method, body)
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

def user_mgmt(current_account, method, existing_users, user_list):
    body = ''
    for user in user_list:
        key = existing_users[user]
        uri = 'https://rest.logentries.com/management/accounts/%s/users/%s' % (current_account['resource-id'], key)
        headers = create_headers(current_account, uri, method, body)
        try:
            response = requests.request(method, uri, data='', headers=headers)
        except requests.exceptions.RequestException as error:
            print error
        if response.status_code == 200:
            print "existing user added: %s" % user
        if response.status_code == 204:
            print "deleted user: %s" % user

def add_new_users_to_account(current_account, method, existing_users, new_list):
    uri = 'https://rest.logentries.com/management/accounts/%s/users' % current_account['resource-id']
    for user in new_list:
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

#Read users file and builds a list of existing users
def get_users(account_map, accounts_info, current_account):
    text_users = []
    users_in_cur_account = []
    try:
        filename = str(current_account) + ".txt"
        with open(filename) as file:
            text_users = file.read().splitlines()
            success = 1
    except IOError:
        print 'Error while reading text file: %s' % filename
    if success == 1:
        try:
            with open("%s_prev_state.txt" % current_account, 'w') as file:
                    for user in text_users:
                        file.write("%s\n" % str(user))
        except IOError:
            print 'Error creating previous state file: %s_prev_state.txt' % current_account
    return text_users

def comparator(account_map, text_users, users_in_cur_account):
    new_list = []
    exist_list = []
    missing_list = []
    for user in text_users:
        if user in account_map:
            exist_list.append(user)
    for user in users_in_cur_account:
        if user not in text_users:
            missing_list.append(user)
    for user in users_in_cur_account:
        if user in exist_list:
            exist_list.remove(user)
    return new_list, exist_list, missing_list

def trail_maker(new_list, exist_list, missing_list, in_account):
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
    if len(sys.argv) > 1 and sys.argv[1] != 'build':
        accounts_info = build_accounts()
        existing_users, accounts_info, amap = build_maps(accounts_info, current_account=None)
        for u in xrange(1, len(sys.argv)):
            in_account = sys.argv[u]
            text_users = get_users(existing_users, accounts_info, in_account)
            users_in_cur_account, b, amap = build_maps(accounts_info, current_account = in_account)
            new_list, exist_list, missing_list = comparator(existing_users, text_users, users_in_cur_account)
            prompt = " Do you want to move forward with these modifications? [y/n]: "
            if len(new_list) > 0:
                print "New users being added: %s" % new_list + '\n' + prompt
                choice = raw_input().lower()
                if choice == 'y':
                    add_new_users_to_account(accounts_info[in_account], 'POST', existing_users, new_list)
            if len(exist_list) > 0:
                print "Existing users being added: %s" % exist_list + '\n' + prompt
                choice = raw_input().lower()
                if choice == 'y':
                    user_mgmt(accounts_info[in_account], 'POST', existing_users, exist_list)
            if len(missing_list) > 0:
                print "Users being deleted: %s" % missing_list + '\n' + prompt
                choice = raw_input().lower()
                if choice == 'y':
                    user_mgmt(accounts_info[in_account], 'DELETE', existing_users, missing_list)
            if len(new_list) == 0 and len(exist_list) == 0 and len(new_list) == 0:
                print "No modifications were made to the account: %s" % in_account
            trail_maker(new_list, exist_list, missing_list, in_account)
    if len(sys.argv) > 1 and sys.argv[1] == 'build':
        accounts_info = build_accounts()
        existing_users, accounts_info, amap = build_maps(accounts_info)
        for account in accounts_info:
            with open(str(account)+'.txt', 'w') as file:
                for user in amap[account]:
                    file.write(user+'\n')
            print "Current state file %s.txt built" % account
    if len(sys.argv) == 1:
        print "No inputs were declared\nPlease refer to the documentation at: https://github.com/alam-r7/LE-Bulk_User_Mgmt/blob/master/README.md"
