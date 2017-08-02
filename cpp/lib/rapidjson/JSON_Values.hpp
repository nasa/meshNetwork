#ifndef _RAPIDJSON_JSON_VALUES_HPP_
#define _RAPIDJSON_JSON_VALUES_HPP_

#include "document.h"

namespace rapidjson
{
    /**
     * This class manages JSON arrays
     */
    class JSON_Values
    {
      public:
        /**
         * Constructor.
         * @param value Array entry from a JSON document.
         */
        JSON_Values(const Value &value);

        /**
         * Retreive a string value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param e Array element number to get from.
         * @return True if the value is found, otherwise, false.
         */
        bool get_string(const char *entry, char **value, unsigned int e) const;

        /**
         * Retreive an integer value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param e Array element number to get from.
         * @return True if the value is found, otherwise, false.
         */
        bool get_int(const char *entry, int &value, unsigned int e) const;

        /**
         * Retreive a double value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param e Array element number to get from.
         * @return True if the value is found, otherwise, false.
         */
        bool get_double(const char *entry, double &value, unsigned int e) const;

        const Value &m_val;
     
    private:
        bool m_valid;

    };
}

#endif // _RAPIDJSON_JSON_VALUES_HPP_
