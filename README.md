# LE-Bulk_User_Mgmt

The Bulk User Management script was created to help users manage their different Logentries accounts, it serves as a CLI replacement for the UI. Each account will be controlled by a text file, with the text file acting as a current state of the account. If a user is added to the text file, that user will be added from the account, if a user is removed from the text file, that user will be removed from the account.

REQUIREMENTS
===================
It is expecting a file called settings.ini in the same directory as the script.

The settings.ini file is expected to be formatted in the following manner, with each stanza representing a separate account:
[Account1]   <---- Account label
api-key-id = $API_KEY_ID
api-key = $API_KEY
resource-id = $RESOURCE_ID

[Account2]
api-key-id = $API_KEY_ID
api-key = $API_KEY
resource-id = $RESOURCE_ID

The script is also expecting Account1.txt, Account2.txt, etc, in the same directory.

GETTING STARTED
==================================
When running the script for the first time, you can run:
python bulk_mgmt.py build

This will build those account text files for you, for all of the accounts given in settings.ini.
The files will be output as Account1_map.txt, Account2_map.txt, etc.

USAGE
===========================================
The script is expecting accounts to be passed as arguments, lets say you have Account1 to Account10. Users were updated for Account2 and Account8, and you want to only update Account2 and Account8. 
You would run:
python bulk_mgmt.py Account2 Account8

**note**, Account labels in settings.ini, Accounts.txt, and Accounts being passed as arguments are all case sensitive.

AUDITING
============================================
The script will output a Account1_prev_state.txt, incase a file was processed accidentally, so you can always restore the previous state of your accounts.

An Account1_trail.txt will be outputted as well, to show you what changes have been made to each account.
