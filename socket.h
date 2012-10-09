#include <sys/types.h>
#include <sys/socket.h>
#include <netdb.h>
#include <netinet/in.h>
#include <string>
#include <iostream>
#include <sstream>
#include <fstream>

#include "urlParser.h"

using namespace std;

string getPathRequest(string);
int connectToServer(string);
bool sendToServer(int, string);
string readFromServer(int);
void downloadFile(string);
void downloadFile(string, string);