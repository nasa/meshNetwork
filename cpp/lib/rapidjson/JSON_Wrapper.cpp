#include "JSON_Wrapper.hpp"
#include "filereadstream.h"
#include <stdio.h>
#include <iostream>
namespace rapidjson {

    bool loadJSONDocument(rapidjson::Document & d, std::string filename) {
        return loadJSONDocument(d, filename.c_str());
    }
    
    bool loadJSONDocument(rapidjson::Document & d, const char *filename) {
        FILE *fp = fopen(filename, "r");
        
        if(NULL == fp)
        {
            perror("fopen");
            return false;
        }

        char readBuffer[65536];
        FileReadStream is(fp, readBuffer, sizeof(readBuffer));
        d.ParseStream(is);
        fclose(fp);

        return true;
    }
       
    int get_size(const rapidjson::Document &d, const char *entry) {
        if(d.HasMember(entry)) {
            return (int)d[entry].Size();
        }

        return 0;
    }

    bool get_string(const rapidjson::Document & d, const char *entry, std::string & value) {
        if(d.HasMember(entry))
        {
            if(d[entry].IsString()) {
                value = d[entry].GetString();
                return true;
            }
        }
        return false;
    }
    
    int get_strings(const rapidjson::Document & d, const char *entry, std::string *value, int numEntries) {
        if(d.HasMember(entry))
        {
            const Value & val = d[entry];
            return get_strings(val, value, numEntries);
        }

        return 0;
    }
    
    

    bool get_int(const rapidjson::Document & d, const char *entry, int &value) {
        if(d.HasMember(entry))
        {
            if(d[entry].IsInt())
            {
                value = d[entry].GetInt();
                return true;
            }
        }

        return false;
    }
    
    int get_ints(const rapidjson::Document & d, const char *entry, int *value, int numEntries) {
        if(d.HasMember(entry))
        {
            const Value & val = d[entry];
            return get_ints(val, value, numEntries);
        }

        return 0;
    }
    
    bool get_int(const rapidjson::Document & d, const char *entry, unsigned int &value) {
        if(d.HasMember(entry))
        {
            if(d[entry].IsUint())
            {
                value = d[entry].GetUint();
                return true;
            }
        }

        return 0;
    }
    
    bool get_bool(const rapidjson::Document & d, const char *entry, bool &value) {
        if(d.HasMember(entry))
        {
            if(d[entry].IsBool())
            {
                value = d[entry].GetBool();
                return true;
            }
        }

        return false;
    }

    bool get_double(const rapidjson::Document & d, const char *entry, double &value) {
        if(d.HasMember(entry))
        {
            if(d[entry].IsDouble())
            {
                value = d[entry].GetDouble();
                return true;
            }
        }

        return false;
    }

    int get_doubles(const rapidjson::Document & d, const char *entry, double *value, int numEntries) {
        if(d.HasMember(entry))
        {
            const Value & val = d[entry];
            if(val.IsArray() && (int)val.Size() <= numEntries) {
                int numDoubles = 0;
                for(rapidjson::SizeType i = 0; i < val.Size(); i++) {
                    if (val[i].IsDouble()) {
                        value[i] = val[i].GetDouble();
                        numDoubles++;
                    }
                    else {
                        return 0;
                    }
                }
                return numDoubles;
            }
        }

        return 0;
    }
    
    int get_size(const rapidjson::Value &v, const char *entry) {
        if(v.HasMember(entry)) {
            return (int)v[entry].Size();
        }

        return 0;
    }

    bool get_string(const rapidjson::Value & v, const char *entry, std::string & value) {
        if(v.HasMember(entry))
        {
            if(v[entry].IsString())
            {
                value = v[entry].GetString();
                return true;
            }
        }

        return false;
    }
    
        
    int get_strings(const rapidjson::Value & v, const char *entry, std::string *value, int numEntries) {
        if(v.HasMember(entry))
        {
            const Value & val = v[entry];
            return get_strings(val, value, numEntries);
        }

        return 0;
    }

    int get_strings(const rapidjson::Value & input, std::string *output, int maxSize) {
        if(input.IsArray() && (int)input.Size() <= maxSize)
        { // Check that value is an array and not bigger than output array
            int numStrings = 0;
            for(rapidjson::SizeType i = 0; i < input.Size(); i++)
            {
                if (input[i].IsString()) {
                    output[i] = input[i].GetString();
                    numStrings++;
                }
                else {
                    return 0;
                }
            }
            return numStrings;
        }   

        return 0;
    }

    
    bool get_int(const rapidjson::Value & v, const char *entry, int &value) {
        if(v.HasMember(entry))
        {
            if(v[entry].IsInt())
            {
                value = v[entry].GetInt();
                return true;
            }
        }

        return false;
    }
    
    bool get_int(const rapidjson::Value & v, const char *entry, unsigned int &value) {
        if(v.HasMember(entry))
        {
            if(v[entry].IsUint())
            {
                value = v[entry].GetUint();
                return true;
            }
        }

        return false;
    }
    
    int get_ints(const rapidjson::Value & v, const char *entry, std::string *value, int numEntries) {
        if(v.HasMember(entry))
        {
            const Value & val = v[entry];
            return get_strings(val, value, numEntries);
        }

        return 0;
    }

    int get_ints(const rapidjson::Value & val, int *value, int numEntries) {
        if(val.IsArray() && (int)val.Size() <= numEntries) {
            int numInts = 0;
            for(rapidjson::SizeType i = 0; i < val.Size(); i++) {
                if (val[i].IsInt()) {
                    value[i] = val[i].GetInt();
                    numInts++;
                }
                else {
                    return 0;
                }
            }
            return numInts;
        }

        return 0;
    }
    
    bool get_bool(const rapidjson::Value & v, const char *entry, bool &value) {
        if(v.HasMember(entry))
        {
            if(v[entry].IsBool())
            {
                value = v[entry].GetBool();
                return true;
            }
        }

        return false;
    }

    bool get_double(const rapidjson::Value & v, const char *entry, double &value) {
        if(v.HasMember(entry))
        {
            if(v[entry].IsDouble())
            {
                value = v[entry].GetDouble();
                return true;
            }
        }

        return false;
    }
    
    int get_doubles(const rapidjson::Value & v, const char *entry, double *value, int numEntries) {
        if(v.HasMember(entry))
        {
            const Value & val = v[entry];
            if(val.IsArray() && (int)val.Size() <= numEntries) {
                int numDoubles = 0; 
                for(rapidjson::SizeType i = 0; i < val.Size(); i++) {
                    if (val[i].IsDouble()) {
                        value[i] = val[i].GetDouble();
                        numDoubles++;
                    }
                    else {
                        return 0;
                    }
                }
                return numDoubles;
            }
        }

        return 0;
    }
    
}

        
    
