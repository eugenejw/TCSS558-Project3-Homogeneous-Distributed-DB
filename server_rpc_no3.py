import pickle
import sys
import re
import os.path
import logging
import datetime
from datetime import datetime
import Pyro4
import os
import json

#
# TCSS 558 - Fall 2014
# Project 3, rcp multi threaded client/server
# File: client_rcp.py
# Authors Wiehan Jiang and Jaylene Sheen
# Date: 11/04/2014
#

class RPC_Server(object):

    def __init__(self, number):
        self.distributed_db_init(number)
        self.pull_mapping_table(number)
        self.self_check(number)
        self.number = number

    def self_check(self, number):
        if not os.path.isfile('database_no%s.db'%number):
           print "[WARNING][%s]DB is empty on Server#%s disk. Will create a default DB on this server." %((str(datetime.now())), number)
           logging.info("[WARNING][%s]DB is empty on Server#%s disk. Default DB has been created on this server." %((str(datetime.now())), number))
           self.db = {'Jaylene%s'%number: '2533550659', 'Weihan%s'%number: '2065197252'}           
           pickle.dump(self.db, open('database_no%s.db'%number, 'wb'))
           
        if (os.path.isfile('database_no%s.db'%number)):
            pass
#           self.db = pickle.load(open('database_no%s.db'%number, 'rb'))   no needed

        self._sync_up_mapping_table(self.mapping_table, self.db, number)
        pickle.dump(self.db, open('database_no%s.db'%number, 'wb'))
        print "[info][%s]Local disk DB updated with DB on memory on server#%s. "%((str(datetime.now())), number)
        logging.info("[info][%s]Local disk DB updated with DB on memory on server#%s." %((str(datetime.now())), number))
#           print '[debug]: the self.db is %s'%self.db
#           print '[debug]: the type of self.db is %s'%type(self.db)
#           print '[debug]: the mapping table is %s'%self.mapping_table
#           print '[debug]: the type of mapping table is %s'%type(self.mapping_table)

    def _sync_up_mapping_table(self, mapping_table, local_db, number):
        dic_map = mapping_table
        dic_local = local_db
        #[for debug purposes]                dic_local['test_name'] = 'test_number'
        temp_dic = {}
        temp_list = []
        for key in dic_map.keys():
            if dic_map[key] == 'server%s'%number:
                temp_dic[key] = 'server%s'%number
                
        if dic_local.viewkeys() == temp_dic.viewkeys():
                print "[info][%s]SELF_TEST: DB on server#%s synced up with mapping table"%((str(datetime.now())), number)
                logging.info("[info][%s]SELF_TEST: DB on server#%s synced up with mapping table" %((str(datetime.now())), number))
        else:
                if list(dic_local.viewkeys() - temp_dic.viewkeys()):
                   for each in list(dic_local.viewkeys() - temp_dic.viewkeys()):
                       self.mapping_table[each] = 'server%s'%number
                       temp_list.append(each)
                   #update the mapping table
                   with open('mapping_table.json', 'w') as f:
                       json.dump(self.mapping_table, f)
                   print '[info][%s]mapping table updated -- new key \'%s\' added to mapping table from server#%s'%((str(datetime.now())), str(temp_list), number)
                   logging.info("[info][%s]mapping table updated -- new key \'%s\' added to mapping table from server#%s"%((str(datetime.now())), str(temp_list), number))
                if list(temp_dic.viewkeys() - dic_local.viewkeys()):
                   for each in list(temp_dic.viewkeys() - dic_local.viewkeys()):
                       del self.mapping_table[each]
                   with open('mapping_table.json', 'w') as f:
                       json.dump(self.mapping_table, f)
                   print '[WARNING][%s]: mapping table contains key -- \'%s\' that does not exist on local DB server#%s. Deleted it.'%((str(datetime.now())), str(list(temp_dic.viewkeys() - dic_local.viewkeys())), number)
                   logging.info('[WARNING][%s]: mapping table contains key -- \'%s\' that does not exist on local DB server#%s. Deleted it.'%((str(datetime.now())), str(list(temp_dic\
.viewkeys() - dic_local.viewkeys())), number))
                   
        
        
    def pull_mapping_table(self, number):
        if not os.path.isfile('mapping_table.json'):
            data = {
                'Jaylene%s'%number : 'server_%s'%number,
                'Weihan%s'%number : 'server_%s'%number,
            }
            with open('mapping_table.json', 'w') as f:
                json.dump(data, f)

        if os.path.isfile('mapping_table.json'):
            with open('mapping_table.json', 'r') as f:
                self.mapping_table = json.load(f)


    def distributed_db_init(self, number):
        # initiate a distributed DB once server gets running

        if not os.path.isfile('database_no%s.db'%number):
           self.db = {'Jaylene%s'%number: '2533550659', 'Weihan%s'%number: '2065197252'}           
           pickle.dump(self.db, open('database_no%s.db'%number, 'wb'))
        if (os.path.isfile('database_no%s.db'%number)):
           self.db = pickle.load(open('database_no%s.db'%number, 'rb'))
        print "[INFO][%s]local DB loaded onto Memory on server#%s."%(str(datetime.now()), number)
        logging.info('[INFO][%s]:local DB loaded onto Memory on server#%s.' %(str(datetime.now()), number))

    def _mapper_input_parser(self):
        #maps the query from client, to check either it is a local operation or an operation on remote DB

        m = re.match(r"(?P<KEY>\w+) (?P<INPUT>.*)", "%s" %self.data)
        if (m.group('KEY') == 'QUERY'):   #query operation
          return 'local' 
        if (m.group('KEY') == 'PUT'):   # put operation
          m1 = re.match(r"(?P<INPUT1>\w+) (?P<INPUT2>\w+)", m.group('INPUT'))
#          return m1.group('INPUT1') 
          return m1.group('INPUT1')
        elif not (m.group('KEY') == 'PUT'): # get and delete operations
          m1 = re.match(r"(?P<INPUT1>\w+)", m.group('INPUT'))
          return m1.group('INPUT1')
        else:
          return 'local'

    def _mapper(self):
        
        query_key=self._mapper_input_parser()
        if query_key == 'local':
            return self.number
        if self.mapping_table.has_key(query_key):
            server=self.mapping_table[query_key]
            pattern=re.compile(r'server(\d)')
            server_number=pattern.search(server).group(1)
            if server_number == self.number:
                return self.number
            else:
                return server_number
        else:
            return 'none'
        


    def _get_data_from_remote_server(self, number, data):
        temp_RPC_Server=Pyro4.Proxy("PYRONAME:server_no%s.tcss558"%number)
        received = temp_RPC_Server.get_request(data)
        return received

    def get_request(self, request):
        print "\n[INFO][%s]+++++++++ new requesting coming in +++++++++" %str(datetime.now())
        logging.info('[INFO][%s]:+++++++++ new requesting coming in ++++++++.' %str(datetime.now()))
        print "[INFO][{0}]Following request coming from Client:".format(str(datetime.now()))
        logging.info('[INFO][{0}]Request coming from Client:'.format(str(datetime.now())))
        #to sync up the mapping table before doing operations
        print "[INFO][{0}]Syncing-Up the mapping table...".format(str(datetime.now()))
        logging.info('[INFO][{0}]Syncing-Up the mapping table...'.format(str(datetime.now())))
        self.pull_mapping_table(self.number)
        self._sync_up_mapping_table(self.mapping_table, self.db, self.number)
        print "[INFO][{0}]Syncing-Up Done...".format(str(datetime.now()))
        logging.info('[INFO][{0}]Syncing-Up Done...'.format(str(datetime.now())))
#        self.db_init()   no longer needed as db has been replaced by distributed db def
        self.data = request
        print "[INFO]Request detail --> \"{0}\"".format(self.data)
        mapper_number=self._mapper()
        parsed_data = self.input_parser()
        if mapper_number == self.number:
            print "[INFO]Operation Level --> Locally on Server#%s"%mapper_number
            sent_back_db_value = self.db_operation(parsed_data)
        elif mapper_number == 'none'and not len(parsed_data) == 3:
            sent_back_db_value = 'The Key you entered is not in any DB of the servers. Please check by using \'QUERY\' command'
        elif mapper_number == 'none'and len(parsed_data) == 3:
            print "[INFO]Operation Level --> Locally on Server#%s"%mapper_number
            sent_back_db_value = self.db_operation(parsed_data)
        else:
            print "[INFO]Operation Level --> Remote Operation on Server#%s"%mapper_number
            sent_back_db_value = self._get_data_from_remote_server(mapper_number, request)
        print "[INFO][%s]Server responding -->  %s" %(str(datetime.now()),sent_back_db_value)
        logging.info("[INFO][%s]Server responding -->  %s" %(str(datetime.now()),sent_back_db_value))
        print "[INFO][%s]+++++++++ this request session completes ++++++++\n" %str(datetime.now())
        logging.info("[INFO][%s]+++++++++ this request session completes ++++++++"%str(datetime.now()))
        return "{0}".format(sent_back_db_value + '(<-- server#%s)'%self.number)

    def replace_acronym(self,a_dict,check_for,replacement_key,replacement_text):
        c = a_dict.get(check_for)
        if c is not None:
          del a_dict[check_for]
          a_dict[replacement_key] = replacement_text
          self.db = a_dict
        elif c is None:
          a_dict[replacement_key] = replacement_text
          print self.db
#        pickle.dump(self.db, open('database_no%s.db'%self.number, 'wb')) not updating the db on disk until sync up happen
        self.self_check(self.number)
        return self.db

    def purge_db(self,a_dict,check_for):
        c = a_dict.get(check_for)
        if c is not None:
          del a_dict[check_for]
          self.db = a_dict
#          pickle.dump(self.db, open('database_no%s.db'%self.number, 'wb')) 
          #update the mapping table
          self.self_check(self.number)
          return_string = "Key/Value Pair of KEY {%s} has been purged from DB" %(check_for)
          return return_string
        elif c is None:
          return_string = "Sorry, Key/Value Pair of KEY {%s} does not exist in any DB." %(check_for)
          return return_string



    def db_operation(self, input):
        # initiate a DB once server gets running
#        self.db = {'Jaylene': '2533550659', 'Weihan': '2065197252'}
        if re.findall(r"error_input", input[0]):
           return 'Invalid Input, now we support four oprands {QUERY|GET arg1|PUT arg1 arg2|DELETE arg1}'
        if re.findall(r"GET", input[0]):
           if (input[1] in self.db): 
              return_string = "The value of KEY \"%s\" is %s" %(input[1],self.db[input[1]])
              return return_string
           else:
              return_string = "The KEY is not in DB. Try {QUERY} or {PUT} to add one." 
              return return_string
        if re.findall(r"PUT", input[0]):
#           self.db[input[1]] = input[2]
           self.replace_acronym(self.db,input[1],input[1],input[2]) 
           return_string = "Key/Value Pair {%s/%s} has been added to DB" %(input[1],input[2])
           return return_string
        if re.findall(r"QUERY", input[0]):
           if input[1] == 'locally':
               return_string = "local DB status: %s"% self.db
               return return_string
           elif input[1] == 'globally': 
               return_string = "Ditributed Databases status: %s"% self.mapping_table
               return return_string
           else:
               return_string = "Argument(s) not recognizable. Enter \'help\' to check valid argument for QUERY."
               return return_string
        if re.findall(r"DELETE", input[0]):
           return_string=self.purge_db(self.db,input[1]) 

           return return_string


    def input_parser(self):
        #parses the query from client, to check either it is a PUT or GET

        m = re.match(r"(?P<KEY>\w+) (?P<INPUT>.*)", "%s" %self.data)
        if (m.group('KEY') == 'QUERY'):   #query operation
          return ['QUERY', m.group('INPUT')] 
        if (m.group('KEY') == 'PUT'):   # put operation
          m1 = re.match(r"(?P<INPUT1>\w+) (?P<INPUT2>\w+)", m.group('INPUT'))
          return [m.group('KEY'),m1.group('INPUT1'),m1.group('INPUT2')] 
        elif not (m.group('KEY') == 'PUT'): # get and delete operations
          return [m.group('KEY'),m.group('INPUT')]
        else:
          return ['error_input']


if __name__=='__main__':
    server_number = '3'
    logging.basicConfig(filename='server_rpc_no%s.log'%server_number, level=logging.INFO)
    server_initializer=RPC_Server(server_number)
#    logger = logging.getLogger('server_rpc_no1.log')
#    logger.setLevel(logging.DEBUG)
#    logger.basicConfig(filename='server_rpc_no1.log', level=logging.DEBUG, filemode='w')
    logging.basicConfig(filename='server_rpc_no%s.log'%server_number, level=logging.INFO)
    print '[info][%s]:Name space \'server_no%s.tcss558\' assigned to server#%s.' %(str(datetime.now()), server_number, server_number)
    logging.info('[info][%s]:Name space \'server_no%s.tcss558\' assigned to server#%s.' %(str(datetime.now()), server_number, server_number))
    os.system("nohup python -m Pyro4.naming &")
    daemon=Pyro4.Daemon()                 # make a Pyro daemon
    ns=Pyro4.locateNS()                   # find the name server
    uri=daemon.register(server_initializer)   # register the object as a Pyro object
    ns.register("server_no%s.tcss558"%server_number, uri)  # register the object with a name in the name server
    print "[info]Server #%s is Up and Running."%server_number
    logging.info('[%s]:Server #%s Started.' %(str(datetime.now()), server_number))
    daemon.requestLoop()                  # start the event loop of the server to wait for calls


