#include "JSON_Value.hpp"
#include "filereadstream.h"

namespace rapidjson
{

    JSON_Value::JSON_Value(const Value &value)
        : m_valid(false)
        , m_val(value)
    {
        m_valid = true;
    }

    bool JSON_Value::get_string(const char *entry, char **value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_val.HasMember(entry))
        {
            if(m_val[entry].IsString())
            {
                *value = const_cast<char *>(m_val[entry].GetString());
                return true;
            }
        }

        return false;
    }

    bool JSON_Value::get_int(const char *entry, int &value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_val.HasMember(entry))
        {
            if(m_val[entry].IsInt())
            {
                value = m_val[entry].GetInt();
                return true;
            }
        }

        return false;
    }

    bool JSON_Value::get_double(const char *entry, double &value) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_val.HasMember(entry))
        {
            if(m_val[entry].IsDouble())
            {
                value = m_val[entry].GetDouble();
                return true;
            }
        }

        return false;
    }

    int JSON_Value::get_doubles(const char *entry, double *value,
                                unsigned int nentries) const
    {
        if(!m_valid)
        {
            return false;
        }

        if(m_val.HasMember(entry))
        {
            const Value &arr = m_val[entry];
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

    double parseDouble(rapidjson::Value &d, const char *entry)
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

    int parseStringArray(rapidjson::Value &d, const char *entry,
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

    int parseDoubleArray(rapidjson::Value &d, const char *entry, double *output,
                         int maxSize)
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
