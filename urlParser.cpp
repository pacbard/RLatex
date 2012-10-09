/*
 * parser.c - HTTP Parser (Sort of...)
 * Apr 12 2001
 * Shaheen Gandhi <sgandhi@andrew.cmu.edu>
 * 
 * Parses an HTTP Requests and Responses
 *
 * If you want to add features to your proxy
 * that requires parsing of HTTP, feel free
 * to edit this file and parser.h
 *
 * We will collect both files.
 */
 
#include <unistd.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "urlParser.h"

method_string supported_methods[] = {{GET, "GET"}};


/* int parse_url(const char *uri, parsed_url **pu)
 *
 * Parses a URL of the form http://<host>[:<port>]/<path>
 * If an input URL is less than 10 characters, it is not
 * valid and an error code is returned.
 * 
 * const char *uri      URL to parse of the above form
 * parsed_url **pu      Information obtained from the URL
 *                      is placed in a parsed_url structure,
 *                      the address of which is returned in pu
 *
 * Returns 0 on success, negative values on error.
 *
 * The caller is required to free the returned structure, unless
 * an error occurred.
 */
int parse_url(const char *uri, parsed_url **pu)
{
  char temp[20];
  int len = uri ? strlen(uri) : 0;
  parse_states state = HOST;
  const char *p = uri + 7, *last = p;
  parsed_url *info = (parsed_url *)malloc(sizeof(parsed_url));
  
  if(!uri || len < 9) {
    free(info);
    return -1;
  }

  if(strncasecmp(uri, "HTTP://", 7)) {
    free(info);
    return -2;
  }
   
  bzero(info, sizeof(parsed_url));
  info->port = DEFAULT_WEBSERVER_PORT;

  while(*p && state != ERROR && state != PATH) {
    switch(*p) {
    case ':':
      if(state == HOST) {
        if(last == p) {
          state = ERROR;
          break;
        }
        
        info->host = (char *)malloc(p - last + 1);
        strncpy(info->host, last, p - last);
        info->host[p - last] = '\0';
        state = PORT;
        last = p + 1;
      } else if(state == PORT) {
        state = ERROR;
      }
      break;
    case '/':
      if(state == HOST) {
        if(last == p) {
          state = ERROR;
          break;
        }
        
        info->host = (char *)malloc(p - last + 1);
        strncpy(info->host, last, p - last);
        info->host[p - last] = '\0';
        state = PATH;
        last = p + 1;
      } else if(state == PORT) {
        if(last == p) {
          state = ERROR;
          break;
        }
        
        bzero(temp, sizeof(temp));
        strncpy(temp, last, p - last);
        info->port = atoi(temp);
        last = p + 1;
        state = PATH;
      }
      break;
    default:
      break;
    }
    p++;
  }
  
  if(state == ERROR) {
    if(info->host)
      free(info->host);
    free(info);
    
    return -3;
  }
  
  if(state == HOST) {
    info->relpath = strdup("");
    info->host = (char *)malloc(p - last + 1);
    strncpy(info->host, last, p - last);
    info->host[p - last] = '\0';
  } else if(state == PORT) {
    bzero(temp, sizeof(temp));
    strncpy(temp, last, p - last);
    info->port = atoi(temp);
    info->relpath = strdup("");
  } else {
    info->relpath = strdup(last);
  }
  
  info->orig_uri = strdup(uri);
    
  if(pu)
    *pu = info;
  else {
    free(info->host);
    free(info->relpath);
    free(info);
  }
  
  return 0;
}

void free_parsed_url(parsed_url **url)
{
  parsed_url *u = url ? *url : NULL;
  
  if(!url || !u)
    return;
  
  if(u->host)
    free(u->host);
  
  if(u->relpath)
    free(u->relpath);
  
  if(u->orig_uri)
    free(u->orig_uri);
  
  free(u);
  *url = NULL;
}