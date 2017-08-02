#ifndef _RAPIDJSON_JSON_VALUE_HPP_
#define _RAPIDJSON_JSON_VALUE_HPP_

#include "document.h"

namespace rapidjson
{
    class JSON_Value
    {
      public:
        /**
         * Constructor.
         * @param value Entry from a JSON document.
         */
        JSON_Value(const Value& value);

        /**
         * Retreive a string value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @return True if the value is found, otherwise, false.
         */
        bool get_string(const char *entry, char **value) const;
    
        /**
         * Retreive an integer value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @return True if the value is found, otherwise, false.
         */
        bool get_int(const char *entry, int &value) const;

        /**
         * Retreive a double value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @return True if the value is found, otherwise, false.
         */
        bool get_double(const char *entry, double &value) const;

        /**
         * Retreive an array of  double value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param nentries The number of maximum number of entries the array
         * can hold is passed in.
         * @return The number of array entries found on success or -1 on
         * failure.
         */
        int get_doubles(const char *entry, double *value,
                        unsigned int nentries) const;

        const Value& m_val;

      private:
        bool m_valid;

    };
}

#endif // _RAPIDJSON_JSON_VALUE_HPP_
