import socket
import signal # Allow socket destruction on Ctrl+C
import sys
import time
import threading
import struct
import time, csv
class WebServer(object):
    """
    Class for describing simple HTTP server objects
    """
    def sendData(self,client,data):
        dataLen = len(data)
        print("the total length of data is{dataLen}".format(dataLen = dataLen))
        totalsent = 0
        sendLengthOne = 5000
        while totalsent < dataLen:
            sent = client.send(data[totalsent:])
            #sent = client.send(data[totalsent:totalsent + sendLengthOne])
            #print("socket option starts here --------------------------------------------")
            self.getTCPInfo(client)
            if sent == 0:
                raise RuntimeError("socket connection broken")
            totalsent = totalsent + sent
            #print(totalsent)

    def getTCPInfo(self, s):
        fmt = "B"*8+"I"*24+"q"*4+"I"*6+"q"*4
        x = struct.unpack(fmt, s.getsockopt(socket.IPPROTO_TCP, socket.TCP_INFO,192))
        print(x[23])
        c_type_int = s.getsockopt(socket.IPPROTO_TCP,socket.TCP_CONGESTION,5)
        #print(c_type_int)
        #fmt_type = "s"
        #c_type = struct.unpack(fmt_type,c_type_int)
        #print(c_type)
    
        #print("the delay is {delay}".format(delay =x[23]))
        #f = csv.writer(open('/tmp/reno-bpf.csv'), 'a')
        #f.writerow([x[23], x[24]])
        
    def __init__(self, port=8080):
        self.host = socket.gethostname().split('.')[0] # Default to any avialable network interface
        self.port = port
        self.content_dir = '/home/yan/tcpEBPF/tcp-options-bpf/tcp-option/webserver/web' # Directory where webpage files are stored

    def start(self):
        """
        Attempts to create and bind a socket to launch the server
        """
        self.socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        try:
            print("Starting server on {host}:{port}".format(host=self.host, port=self.port))
            self.socket.bind(('', self.port))
            print("Server started on port {port}.".format(port=self.port))

        except Exception as e:
            print("Error: Could not bind to port {port}".format(port=self.port))
            self.shutdown()
            sys.exit(1)
        print("start to listen on port {port}".format(port=self.port))
        self._listen() # Start listening for connections

    def shutdown(self):
        """
        Shuts down the server
        """
        try:
            print("Shutting down server")
            self.socket.shutdown(socket.SHUT_RDWR)

        except Exception as e:
            pass # Pass if socket is already closed

    def _generate_headers(self, response_code):
        """
        Generate HTTP response headers.
        Parameters:
            - response_code: HTTP response code to add to the header. 200 and 404 supported
        Returns:
            A formatted HTTP header for the given response_code
        """
        header = ''
        if response_code == 200:
            header += 'HTTP/1.1 200 OK\n'
        elif response_code == 404:
            header += 'HTTP/1.1 404 Not Found\n'

        time_now = time.strftime("%a, %d %b %Y %H:%M:%S", time.localtime())
        header += 'Date: {now}\n'.format(now=time_now)
        header += 'Server: Simple-Python-Server\n'
        header += 'Connection: close\n\n' # Signal that connection will be closed after completing the request
        return header

    def _listen(self):
        """
        Listens on self.port for any incoming connections
        """
        self.socket.listen(5)
        while True:
            (client, address) = self.socket.accept()
            client.settimeout(60)
            print("Recieved connection from {addr}".format(addr=address))
            threading.Thread(target=self._handle_client, args=(client, address)).start()

    def _handle_client(self, client, address):
        """
        Main loop for handling connecting clients and serving files from content_dir
        Parameters:
            - client: socket client from accept()
            - address: socket address from accept()
        """
        PACKET_SIZE = 1024
        while True:
            print("CLIENT",client)
            data = client.recv(PACKET_SIZE).decode() # Recieve data packet from client and decode
            print("data is {data}".format(data = data))
            if not data: break

            request_method = data.split(' ')[0]
            print("Method: {m}".format(m=request_method))
            print("Request Body: {b}".format(b=data))

            if request_method == "GET" or request_method == "HEAD":
                # Ex) "GET /index.html" split on space
                
                file_requested = data.split(' ')[1]

                # If get has parameters ('?'), ignore them
                file_requested =  file_requested.split('?')[0]

                if file_requested == "/":
                    file_requested = "/index.html"

                filepath_to_serve = self.content_dir + file_requested
                print("file to serve: {filePath}".format(filePath = filepath_to_serve))
                print("Serving web page [{fp}]".format(fp=filepath_to_serve))

                # Load and Serve files content
                try:
                    f = open(filepath_to_serve, 'rb')
                    if request_method == "GET": # Read only for GET
                        response_data = f.read()
                    f.close()
                    response_header = self._generate_headers(200)

                except Exception as e:
                    print("File not found. Serving 404 page.")
                    response_header = self._generate_headers(404)

                    if request_method == "GET": # Temporary 404 Response Page
                        response_data = b"<html><body><center><h1>Error 404: File not found</h1></center><p>Head back to <a href={fileName}>dry land</a>.</p></body></html>".format(fileName = filepath_to_serve)

                response = response_header.encode()
                if request_method == "GET":
                    response += response_data

                #dataSent = client.send(response)
                self.sendData(client, response)
                #print("number of data send:{dataSent}".format(dataSent = dataSent))

                #print(client.getsockopt(socket.IPPROTO_TCP,socket.TCP_INFO))
                #print(client)
                client.close()
                break
            else:
                print("Unknown HTTP request method: {method}".format(method=request_method))
