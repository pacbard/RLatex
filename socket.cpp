#include "socket.h"

string getPathRequest(string host, string path){
	stringstream request;
	
	request << "GET /"<< path << " HTTP/1.0" << endl;
	request << "User-Agent: RemoteLatex/0.1" << endl;
	request << "Host: " << host << endl;
	request << endl << endl;
	
	return request.str();
}

int connectToServer(string host) {
		int sockid;
		struct sockaddr_in socketaddr;
		struct hostent *hostaddr;
		struct servent *servaddr;
		struct protoent *protocol;
		string prot = "tcp";
		string serv = "http";

	/* Resolve the host name */
		if (!(hostaddr = gethostbyname(host.c_str()))) {
			cout << "Error resolving host." << endl;
			exit(1);
		}

	/* clear and initialize socketaddr */
		memset(&socketaddr, 0, sizeof(socketaddr));
		socketaddr.sin_family = AF_INET;

	/* setup the servent struct using getservbyname */
		servaddr = getservbyname(serv.c_str(), prot.c_str());
		socketaddr.sin_port = servaddr->s_port;

		memcpy(&socketaddr.sin_addr, hostaddr->h_addr, hostaddr->h_length);

	/* protocol must be a number when used with socket()
		since we are using tcp protocol->p_proto will be 0 */
			protocol = getprotobyname(prot.c_str());

		sockid = socket(AF_INET, SOCK_STREAM, protocol->p_proto);
		if (sockid < 0) {
			cout << "Error creating socket." << endl;
			exit(1);
		}

	/* everything is setup, now we connect */
		if(connect(sockid, (struct sockaddr*)&socketaddr, sizeof(socketaddr)) == -1) {
			cout << "Error connecting." << endl;
			exit(1);
		}
		return sockid;
}

bool sendToServer(int sockid, string request) {
	/* send our get request for http */
	if (send(sockid, request.c_str(), request.length(), 0) == -1) {
		cout << "Error sending data." << endl;
		return false;
	}
	return true;
}

string readFromServer(int sockid) {
	/* read the socket until its clear then exit */
	int bufsize;
	char buffer[512];
	string response = string();
	while ( (bufsize = read(sockid, buffer, sizeof(buffer)-1))) {
		response.append(buffer, bufsize);
	}
	return response;
}

void downloadFile(string url) {
	downloadFile(url, string());
}

void downloadFile(string uri, string filename) {
	parsed_url *url = new parsed_url;
	parse_url(uri.c_str(), &url);
	
	int sockid = connectToServer(string(url->host));
	sendToServer(sockid, getPathRequest(url->host, url->relpath));
	string response = readFromServer(sockid);
	close(sockid);
	
	response = response.substr(response.find("\r\n\r\n")+4);
	
	if (!filename.empty()) {
		ofstream f;
		f.open(filename.c_str());
		f << response << endl;
		f.close();
	} else {
		cout << response << endl;
	}
	free_parsed_url(&url);
	delete url;
}