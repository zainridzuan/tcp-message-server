# tcp-message-server
A simple TCP server that allows multi-threaded connections from clients, as well as direct P2P connections. 

Users can message each other in a public room, as well as create private rooms to message in too. Users can register credentials which will be saved for future login. 

## Commands
### BCM
- Broadcast message
- usage: BCM [message]
### ATU
- Download active users
- usage: ATU
### SRB
- Separate room building
- usage: SRB [username1] [username2] ...
### SRM
- Separate room message
- usage: SRM [room_id] [message]
### RDM
- Read messages
- message type is either b or s, for broadcast messages or separate room messages
- usage: RDM [message_type] [timestamp]
### OUT
- Logout
- usage: OUT
