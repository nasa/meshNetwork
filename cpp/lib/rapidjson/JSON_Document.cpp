#include "JSON_Document.hpp"
#include "JSON_Value.hpp"
#include "JSON_Values.hpp"
#include "filereadstream.h"

namespace rapidjson
{
    JSON_Document::JSON_Document(const char *filename)
        : m_valid(false)
    {
        FILE *fp = fopen(filename, "r");
        if(NULL == fp)
        {
            perror("fopen");
            return;
        }

        char readBuffer[65536];
        FileReadStream is(fp, readBuffer, sizeof(readBuffer));
        m_doc.ParseStream(is);
        fclose(fp);

        m_valid = true;
    }

    JSON_Value *JSON_Document::get_value(const char *entry) const
    {
        if(!m_valid)
        {
            return NULL;
        }

        if(m_doc.HasMember(entry))
        {
            return new JSON_Value(m_doc[entry]);
        }

        return NULL;
    }

    JSON_Values* JSON_Document::get_values(const char *entry) const
    {
        if(!m_valid)
        {
            return NULL;
        }

        if(m_doc.HasMember(entry))
        {
            return new JSON_Values(m_doc[entry]);
        }

        return NULL;
    }

    bool JSON_Document::get_string(const char *entry, char value[],
                                   unsigned int nbytes) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            if(m_doc[entry].IsString())
            {
                strncpy(value, m_doc[entry].GetString(), nbytes);
                return true;
            }
        }

        return false;
    }

    bool JSON_Document::get_int(const char *entry, int &value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            if(m_doc[entry].IsInt())
            {
                value = m_doc[entry].GetInt();
                return true;
            }
        }

        return false;
    }

    int JSON_Document::get_ints(const char *entry, int *value,
                                   unsigned int nentries) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            const Value &arr = m_doc[entry];
            if(arr.IsArray() && (arr.Size() <= nentries))
            {
                for(unsigned int i = 0; i < arr.Size(); ++i)
                {
                    value[i] = arr[i].GetInt();
                }
                return arr.Size();
            }
        }

        return -1;
    }

    bool JSON_Document::get_bool(const char *entry, bool &value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            if(m_doc[entry].IsBool())
            {
                value = m_doc[entry].GetBool();
                return true;
            }
        }

        return false;
    }

    bool JSON_Document::get_double(const char *entry, double &value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            if(m_doc[entry].IsDouble())
            {
                value = m_doc[entry].GetDouble();
                return true;
            }
        }

        return false;
    }

    int JSON_Document::get_doubles(const char *entry, double *value,
                                   unsigned int nentries) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_doc.HasMember(entry))
        {
            const Value &arr = m_doc[entry];
            if(arr.IsArray() && (arr.Size() <= nentries))
            {
                for(unsigned int i = 0; i < arr.Size(); ++i)
                {
                    value[i] = arr[i].GetDouble();
                }
                return arr.Size();
            }
        }

        return -1;
    }

    double parseDouble(rapidjson::Document &d, const char *entry)
    {
        if(d.HasMember(entry))
        {
            if(d[entry].IsDouble())
            {
                return d[entry].GetDouble();
            }
        }
        return 0;
    }

    int parseStringArray(rapidjson::Document &d, const char *entry,
                         const char **output, int maxSize)
    {
        if(d.HasMember(entry))
        {
            const rapidjson::Value &arr = d[entry];
            if(arr.IsArray() && (int)arr.Size() <= maxSize)
            { // Check that value is an array and not bigger than output array
                for(rapidjson::SizeType i = 0; i < arr.Size(); i++)
                {
                    output[i] = arr[i].GetString();
                }
                return arr.Size();
            }
        }

        return 0;
    }

    int parseDoubleArray(rapidjson::Document &d, const char *entry,
                         double *output, int maxSize)
    {
        if(d.HasMember(entry))
        {
            const rapidjson::Value &arr = d[entry];
            if(arr.IsArray() && (int)arr.Size() <= maxSize)
            { // Check that value is an array and not bigger than output array
                for(rapidjson::SizeType i = 0; i < arr.Size(); i++)
                {
                    output[i] = arr[i].GetDouble();
                }
                return arr.Size();
            }
        }

        return 0;
    }
}
