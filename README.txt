README!

Tommy Inouye
ti2181
Networks
Programming Assignment 2

ASSUMPTION: THE EDGES ARE DIRECTED AND TWO NODES CAN HAVE TWO DIFFERENT COSTS TO ANOTHER. A LINKDOWN WILL ONLY CLOSE A LINK FROM SOURCE TO NEIGHBOR AND WILL NOT CLOSE THE EDGE FROM NEIGHBOR TO SOURCE


a: My code works as specified. When you initiate the code using the config file, the program will read the config file and parse out the assigned port number, file name, and file sequence number. Then the rest of the file specifies the neighbors of the host and their associated weight and port number. The program will read that file and create nodes for the assigned neighbors. Then it will use Bellman Ford’s algorithm to figure out the shortest distance to all the nodes in the network. A time is used to broadcast the current distance to every node to every neighbor, and when a neighbor receives an update, it can expand it’s network and shortest cost accordingly. 

b. My program is written in python. Also I used various libraries to help me meet my goals. I used a json library to send arrays through sockets, as well as the base64 library to properly encode and decode the files that we had to read using transfer. Also the time, threading and type libraries were used to keep track of time, consistently use a resettable and repeatable timer, and keep track of the type of files being transferred over. 

c/d/e. My code can be run by calling:

python bfclient.py config

where config file is in the format: 
1112 5 chunk2 2
160.39.231.219:1110 69 
160.39.231.219:1111 20.5
160.39.231.219:1114 40

where 1112 is the port number, 5 is the time out, chunk2 is the file and 2 is the sequence number for the chunk

The commands are as follows:

Linkdown: Will close a link to a neighbor for the user. SO it will set the cost to that neighbor to infinity and let rest of the neighbors know that the cost has been changed. I assumed that linkdown will not cause the path from the neighbor back to source to close because I assumed that these were independent of each other since we specified them differently in the config files. 

Command: LINKDOWN IP-ADDRESS PORTNUMBER

Linkup: This will restore any link that was link downed. So a given node must have been Link downed previously and being restored.

Command: LINKUP IP-ADDRESS PORTNUMBER NEWCOST

Showrt: This is very straight forward and will create a table of the address, cost and next hop of every node in your network. 

Command: SHOWRT

Close: This will just close the node and close the socket and terminate the program

Command: CLOSE

Transfer: This will send the file that you were assigned to a given node in your network. It reads a file in 1024 byte chunks and sends these chunks with a sequence number that is read and stored in a dictionary at the destination. Any immediate nodes will just transfer the data to the next neighbor in the path until it reaches the destination.

Command: TRANSFER IPADDRESS PORTNUMBER

EXTRA CREDIT

Transfer: I modified the program so that instead of only 2 chunks, I can determine how many chunks I would like to receive at the beginning of the file. So when the program is run, the user is prompted how many chunks you would like to receive. This will allow the user to receive as many chunks as they want to accommodate for any size file. 

Sendchunk: This will send a chunk that you have already received to another node. You must have already received it. The parameters is the given host name and port number as well as the sequence number of the chunk.

Command: SENDCHUNK IPADDRESS PORTNUMBER CHUNKSEQUENCE NUMBER 





