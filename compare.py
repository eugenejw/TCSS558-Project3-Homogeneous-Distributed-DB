import json

with open('mapping_table', 'r') as f:
    json_obj=json.load(f)

dic1 = {'a':'1','b':'1','c':'2'}
dic2 = {'a':'data','a':'datat','d':'data'}
new_dic1 = {}
for key in dic1.keys():
    if dic1[key] == '1':
       new_dic1[key] = '1'

if dic2.viewkeys() == new_dic1.viewkeys():
    print "db on server 1 is already synced up with mapping table"

if  list(dic2.viewkeys() - new_dic1.viewkeys()):
    for each in list(dic2.viewkeys() - new_dic1.viewkeys()):
        json_obj[each] = 'server_TEST'
        print json_obj
        
    
