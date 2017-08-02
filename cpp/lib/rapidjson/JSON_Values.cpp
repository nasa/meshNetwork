#include "JSON_Values.hpp"
#include "filereadstream.h"

namespace rapidjson
{

    JSON_Values::JSON_Values(const Value &value)
        : m_valid(false)
        , m_val(value)
    {
        m_valid = true;
    }

    bool JSON_Values::get_string(const char *entry, char **value,
                                 unsigned int e) const
    {
        if(!m_valid || (m_val.Size() <= e))
        {
            return false;
        }

        if(m_val[e].HasMember(entry))
        {
            if(m_val[e][entry].IsString())
            {
                *value = const_cast<char *>(m_val[e][entry].GetString());
                return true;
            }
        }

        return false;
    }

    bool JSON_Values::get_int(const char *entry, int &value,
                              unsigned int e) const
    {
        if(!m_valid || (m_val.Size() <= e))
        {
            return false;
        }

        if(m_val[e].HasMember(entry))
        {
            if(m_val[e][entry].IsInt())
            {
                value = m_val[e][entry].GetInt();
                return true;
            }
        }

        return false;
    }

    bool JSON_Values::get_double(const char *entry, double &value,
                                 unsigned int e) const
    {
        if(!m_valid || (m_val.Size() <= e))
        {
            return false;
        }

        if(m_val[e].HasMember(entry))
        {
            if(m_val[e][entry].IsDouble())
            {
                value = m_val[e][entry].GetDouble();
                return true;
            }
        }

        return false;
    }
}
