#ifndef _PARSER_H_
#define _PARSER_H_

#define DEFAULT_WEBSERVER_PORT      (80)
#define NUM_METHODS                 ((sizeof(supported_methods)) / (sizeof(method_string)))
#define BUFSIZE                     (1024)

/* You don't have to worry about parse_states
 * but you should worry about parse_error
 *
 * PERR_NONE      Returned when everything works fine
 *
 * PERR_NOT_IMPLEMENTED
 *                Returned when the method of the HTTP Request
 *                is not GET
 *
 * PERR_BAD_REQUEST
 *                Returned if the request is not parseable
 *
 * PERR_INTERNAL_ERROR
 *                Returned when an internal error (such as malloc
 *                returns NULL) occurs.
 */
typedef enum _parse_states {HOST, PORT, PATH, ERROR} parse_states;
typedef enum _parse_error {PERR_NONE = 0, PERR_NOT_IMPLEMENTED, PERR_BAD_REQUEST, PERR_INTERNAL_ERROR} parse_error;

/* If you want to add more HTTP methods,
 * for instance, POST or PUT, declare them
 * inside http_method, and create an entry for
 * it in the supported_methods array in parser.c
 *
 * But you'll have to add the rest of the functionality
 * yourself..
 */
typedef enum _http_method {GET} http_method;

/* The only structures you have to worry
 * about are parsed_request and parsed_url
 *
 * See the lab handout for more info
 */
typedef struct _method_string {
  http_method method;
  const char *s;
} method_string;

typedef struct _parsed_url {
  char *host, *relpath, *orig_uri;
  int port;
} parsed_url;

/* Don't worry about this either */
extern method_string supported_methods[];

int parse_url(const char *uri, parsed_url **pu);
void free_parsed_url(parsed_url **url);
#endif