from operator import itemgetter

channel_index = 0
rank_index = 1
bank_index = 2
row_index = 3
column_index = 4

page_policy = 1
# close page = 0
# open page = 1

file = open("dram_cmd.csv")
lines = file.readlines()
file.close()
lines.pop(0)

lines_u = []
for line in lines:
    line = line.split(",")
    line[6] = line[6][0:-1]
    if(line[7][-1] == '\n' ):  line[7] = line[7][0:-1]
    line[0] = int(line[0])
    line[1] = int(line[1])
    line[2] = int(line[2])
    line[3] = int(line[3])
    line[4] = int(line[4])
    line[5] = int(line[5])
    line[6] = int(line[6])
    lines_u.append(line)

lines_u = sorted(lines_u, key=itemgetter(6))

for line in lines_u:
    print(line)
    
#if(line[0] == '0'): print(int(line[0])+int(line[1]))

def max_value(lines, index):
    max_val = 0
    for line in lines:
        max_val = max(int(line[index]), max_val)
    return max_val

max_channel = max_value(lines_u,channel_index) + 1
max_rank = max_value(lines_u,rank_index) + 1
max_bank = max_value(lines_u,bank_index) + 1
max_row = max_value(lines_u,row_index) + 1
max_column = max_value(lines_u,column_index) + 1
max_digit_column = len(str(max_column)) + 1
#print(max_channel,max_rank, max_bank, max_row, max_column)

def unique_bank_index(line):
    #print(line)
    #print(channel_index,rank_index, bank_index)
    return int(line[channel_index])*max_rank*max_bank + int(line[rank_index])*max_bank + int(line[bank_index])

def unique_address(line):
    return int(line[row_index])*(10**max_digit_column) + int(line[column_index])

#print(lines_u[0])

#tried =lines_u[0]
#print(unique_bank_index(tried),unique_address(tried) )

unique_banks = max_channel*max_rank*max_bank
buffer_size = 8


########################################################
##
## Simple Row buffer implementation to count PRE, ACT, CAS
##
########################################################


n_act = 0
n_cas = 0
n_pre = 0

row_buffer = [-1]*unique_banks

p_index = 0
row_address = 0

if(page_policy == 1):                               ## Open page poilcy

    for line in lines_u:
        p_index = unique_bank_index(line)
        row_address = line[row_index]

        if(row_buffer[p_index] == -1 ):          #  page empty case
            row_buffer[p_index] = row_address
            n_act = n_act +1
            n_cas = n_cas +1
        
        elif(row_buffer[p_index] == row_address):    # page hit case
            n_cas = n_cas +1
        
        elif(row_buffer[p_index] != row_address):    # page conflit case
            row_buffer[p_index] = row_address
            n_pre = n_pre + 1
            n_act = n_act + 1
            n_cas = n_cas + 1


if(page_policy == 0):                               ## Close page poilcy

    for line in lines_u:
        p_index = unique_bank_index(line)
        row_address = line[row_index]

        if(row_buffer[p_index] == -1 ):          #  page empty case
            n_act = n_act +1
            n_cas = n_cas +1
            n_pre = n_cas +1
        
        elif(row_buffer[p_index] == row_address):    # page hit case
            n_act = n_act +1
            n_cas = n_cas +1
            n_pre = n_cas +1
        
        elif(row_buffer[p_index] != row_address):    # page conflit case
            n_act = n_act +1
            n_cas = n_cas +1
            n_pre = n_cas +1

print("Pre = ", n_pre,"ACT = ", n_act,"CAS =", n_cas)



########################################################
##
## Implemeting row buffer with banks based prefetcher
##
########################################################

u_act = 0
u_cas = 0
u_pre = 0
u_buffer = 0



#Functions for prefetcher
def check_address(line,address):
    return address in line

def remove_address(line,address):
    line.remove(address)

def push_to_front(line, value):
    line.insert(0,value)

def delete_last_value(line):
    line.pop()

# delete from here
address = -1
p_index = -1

"""
# Implementing LRU for all incoming values
for line in lines_u:
    #print(line)
    p_index = unique_bank_index(line)
    address = unique_address(line)
    
    if(check_address(line,address)):
        remove_address(line,address)
        push_to_front(line,address)
    else:
        delete_last_value(line)
        push_to_front(line,address)
#delete upto here
"""

row_buffer = [-1]*unique_banks
prefetcher = [[-1]*buffer_size]*unique_banks

print(prefetcher)
p_index = -1
address = -1
row_address = -1

if(page_policy == 1):                             ## Open page poilcy

    for line in lines_u:
        p_index = unique_bank_index(line)
        address = unique_address(line)
        row_address = line[row_index]
        #print(line,p_index)

        if(row_buffer[p_index] == -1 ):          #  page empty case
            row_buffer[p_index] = row_address

            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer +1
            
            else:            
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                u_act = u_act + 1
                u_cas = u_cas + 1
        
        elif(row_buffer[p_index] == address):    # page hit case
            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer + 1
            
            else:           
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                u_cas = u_cas + 1
        
        elif(row_buffer[p_index] != address):    # page conflit case
            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer + 1
            
            else:           
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                row_buffer[p_index] = address
                u_pre = u_pre + 1
                u_act = u_act + 1
                u_cas = u_cas + 1

if(page_policy == 0):                             ## close page poilcy

    for line in lines_u:
        p_index = unique_bank_index(line)
        address = unique_address(line)
        row_address = line[row_index]

        if(row_buffer[p_index] == -1 ):          #  page empty case
            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer + 1

            else:            
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                u_act = u_act + 1
                u_cas = u_cas + 1
                u_pre = u_pre + 1

        elif(row_buffer[p_index] == address):    # page hit case
            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer +1
            
            else:           
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                u_act = u_act + 1
                u_cas = u_cas + 1
                u_pre = u_pre + 1
        
        elif(row_buffer[p_index] != address):    # page conflit case
            if(check_address(prefetcher[p_index],address)):
                remove_address(prefetcher[p_index],address)
                push_to_front(prefetcher[p_index],address)
                u_buffer = u_buffer +1
            
            else:           
                delete_last_value(prefetcher[p_index])
                push_to_front(prefetcher[p_index],address)
                u_act = u_act + 1
                u_cas = u_cas + 1
                u_pre = u_pre + 1

print("Pre =",u_pre,"ACT =",u_act ,"CAS =", u_cas,"Buffer =", u_buffer)
