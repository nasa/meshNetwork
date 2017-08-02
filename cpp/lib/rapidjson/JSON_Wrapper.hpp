
#include "document.h"

namespace rapidjson {

    bool loadJSONDocument(rapidjson::Document & d, std::string fileName);
    bool loadJSONDocument(rapidjson::Document & d, const char *fileName);
    
    int get_size(const rapidjson::Document &d, const char *entry);
    bool get_string(const rapidjson::Document & d, const char *entry, std::string & value);
    int get_strings(const rapidjson::Document & d, const char *entry, std::string *value, int numEntries);
    bool get_int(const rapidjson::Document & d, const char *entry, int &value);
    int get_ints(const rapidjson::Document & d, const char *entry, int *value, int numEntries);
    bool get_bool(const rapidjson::Document & d, const char *entry, bool &value);
    bool get_double(const rapidjson::Document & d, const char *entry, double &value);
    int get_doubles(const rapidjson::Document & d, const char *entry, double *value, int numEntries);
    
    int get_size(const rapidjson::Value &v, const char *entry);
    bool get_string(const rapidjson::Value & v, const char *entry, std::string & value);
    int get_strings(const rapidjson::Value & v, const char *entry, std::string *value, int numEntries);
    int get_strings(const rapidjson::Value & input, std::string *output, int maxSize);
    bool get_int(const rapidjson::Value & v, const char *entry, int &value);
    bool get_int(const rapidjson::Value & v, const char *entry, unsigned int &value);
    int get_ints(const rapidjson::Value & v, const char *entry, int *value, int numEntries);
    int get_ints(const rapidjson::Value & v, int *value, int numEntries);
    bool get_bool(const rapidjson::Value & v, const char *entry, bool &value);
    bool get_double(const rapidjson::Value & v, const char *entry, double &value);
    int get_doubles(const rapidjson::Value & v, const char *entry, double *value, int numEntries);
}
