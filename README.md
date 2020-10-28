## Server documentation
### Starting the server
To start the server run the `server.py` file and specify the port number you would like your server using the following format
```
path> python server.py [port]
```

The server uses standard Python libraries `socket`, `select`, `sys` and `pickle`  so it should run with a standard Python installation (version 3.5 or above).

### Shutdown the server
The server can be shutdown using the keyboard interrupt `ctrl`+`c`  after which it closes all active connections and exits.

## Client documentation
### Connecting to the server
To connect to the server run the `client.py` file and specify 
- The username you would like to connect as 
- The hostname (IPV4 address) of the server
- The port number of the server
using the following format
```bash
path> python client.py [username] [hostname] [port]
```
### Sending messages
1. Group messages : Simply type in the body of your message after the prompt as messages are sent to everyone by default unless specified otherwise.
2. Private messages : Prefixed by a '@' type in the username of the person you would like to send a message to, followed by a space and the body of your message i.e. in the following format
   ```
   @username Your message to 'username' here.
   ```
 ### Available commands
 The functionalty of the commads below is accesible by typing the command after the prompt.
| Command     | Description |
| ----------- | ----------- |
| `--help`  |Display the help text. This text is also displayed at the beginning when the user joins the server.|
| `--list` |List all other current users.     |
| `--changeName [new username]`  |Change your username.|
| `--leave`  |Leave the server. |

 