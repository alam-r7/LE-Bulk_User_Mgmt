# LE-Bulk_User_Mgmt

The Bulk User Management script was created to help users manage their different Logentries accounts, it serves as a CLI replacement for account management via the UI. Each account will be controlled by a text file, with the text file acting as a current state of the account. If a user is added to the text file, that user will be added from the account, if a user is removed from the text file, that user will be removed from the account.  

REQUIREMENTS
===================
It is expecting a file called settings.ini in the same directory as the script.  

The settings.ini file is expected to be formatted in the following manner, with each stanza representing a separate account:  
[Your_Account1] <--- Alter the labels to reflect your account name   
api-key-id = $API_KEY_ID  
api-key = $API_KEY  
resource-id = $RESOURCE_ID  

[Your_Account2]    
api-key-id = $API_KEY_ID  
api-key = $API_KEY  
resource-id = $RESOURCE_ID  

[Your_Account3]
api-key-id = $API_KEY_ID  
api-key = $API_KEY  
resource-id = $RESOURCE_ID    

To get your API keys/Resource ID:
![Screenshot](https://github.com/alam-r7/LE-Bulk_User_Mgmt/blob/master/doc/Step%201%20-%20Getting%20API%20Keys.png?raw=true)
**Note:** API_KEY_ID is only displayed when the API Key is first generated

GETTING STARTED
==================================
After you've created settings.ini with all of the accounts that you're hoping to manage via CLI.
You can run:  
python bulk_user_mgmt.py build

This will build text files for you, with the current list of users for each account, for the accounts given in settings.ini.
The files will be output as Your_Account1.txt, Your_Account2.txt, Your_Account3.txt, etc, so they can be easily modified.  

USAGE
===========================================
The script is expecting accounts to be modified as arguments, lets say you have Account1 to Account10. 
You updated the text files for Account2.txt and Account8.txt, and you want to only update Account2 and Account8.    
You would run:  
python bulk_user_mgmt.py Account2 Account8  
  
**Note:** Account labels in settings.ini, Accounts.txt, and Accounts being passed as arguments are all case sensitive.  

AUDITING
============================================
The script will output a Account1_prev_state.txt, incase a file was processed accidentally, so you can always restore the previous state of your accounts by removing \_prev_state from the filename.  
  
An Account1_trail.txt will be outputted as well, to show you what changes have been made to each account.  
