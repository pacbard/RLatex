#include <iostream>
#include <fstream>
#include <sstream>
#include <string>
#include <stdio.h>

#ifdef WIN32 // For xmlParser
#define _CRT_SECURE_NO_DEPRECATE
#endif

#include "socket.h"
#include "xmlparser.h"
#include "main.h"

using namespace std;

string readFile(string filename) {
	string buf, line;
	ifstream file(filename.c_str());
	while(getline(file,line)) {
		buf += line;
		buf += "\n";
	}
	file.close();
	return buf;
}

string convertInt(int number)
{
   stringstream ss;//create a stringstream
   ss << number;//add number to the stream
   return ss.str();//return a string with the contents of the stream
}

string buildRequest(string filename) {
	stringstream request;
		
	XMLNode xml = XMLNode::createXMLTopNode("xml",TRUE);
	xml.addAttribute("version","1.0");
	xml.addAttribute("encoding","UTF-8");
	XMLNode compile = xml.addChild("compile");
	XMLNode token = compile.addChild("token");
	token.addText(token);
	XMLNode resources = compile.addChild("resources");
	resources.addAttribute("root-resource-path", filename.c_str());
	XMLNode resource = resources.addChild("resource");
	resource.addAttribute("path", filename.c_str());
	resource.addClear(readFile(filename).c_str());
	
	
	string body = xml.createXMLString(FALSE);
	
	request << "POST " << api_url << " HTTP/1.0" << endl;
	request << "User-Agent: RemoteLatex/0.1" << endl;
	request << "Content-Length: " << convertInt(body.length()) << endl;
	request << "Content-Type: text/xml; charset=\"utf-8\"" << endl;
	request << endl;
	request << body;
	request << endl << endl;
	
	return request.str();
}

void  decodeRequest(string response, string filename) {
	XMLNode xml = XMLNode::parseString(response.c_str());
	
	string status(xml.getChildNode("xml").getChildNode("compile").getChildNode("status").getText());
	
	cout << "Compilation status: " << status << endl;
	
	downloadFile(xml.getChildNode("xml").getChildNode("compile").getChildNode("logs").getChildNode("file").getAttribute("url"));
	
	if (status.compare("success") == 0) {
		string file = filename.substr(0, filename.rfind("."));
		file += ".pdf";
		downloadFile(xml.getChildNode("xml").getChildNode("compile").getChildNode("output").getChildNode("file").getAttribute("url"), file);
	}		
	}

int main(int argc, char *argv[]) {
	int sockid = connectToServer(server);
	
	string request = buildRequest(argv[1]);
	
	sendToServer(sockid, request);
	string response = readFromServer(sockid);
	close(sockid);
		
	decodeRequest(response, string(argv[1]));
	return (0);
}

