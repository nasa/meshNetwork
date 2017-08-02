#ifndef _RAPIDJSON_JSON_DOCUMENT_HPP_
#define _RAPIDJSON_JSON_DOCUMENT_HPP_

#include "document.h"

namespace rapidjson
{
    // Forward declaration
    class JSON_Value;
    class JSON_Values;

    class JSON_Document
    {
      public:
        /**
         * Constructor.
         * @param filename JSON file to manage.
         */
        JSON_Document(const char *filename);

        /**
         * Get an entry from the JSON file.
         * @param entry The key of the value being searched for.
         * @return A value JSON entry on success or NULL on failure.
         */
        JSON_Value *get_value(const char *entry) const;

        /**
         * Get an array of entries from the JSON file.
         * @param entry The key of the value being searched for.
         * @return A value JSON entry on success or NULL on failure.
         */
        JSON_Values *get_values(const char *entry) const;

        /**
         * Retreive a string value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param nbytes Number of bytes available in the return value array.
         * @return True if the value is found, otherwise, false.
         */
        bool get_string(const char *entry, char value[],
                        unsigned int nbytes) const;

        /**
         * Retreive an integer value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @return True if the value is found, otherwise, false.
         */
        bool get_int(const char *entry, int &value) const;

        /**
         * Retreive an array of int value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @param nenetries The number of maximum number of entries the array
         * can hold is passed in.
         * @return The number of array entries found on success or -1 on
         * failure.
         */
        int get_ints(const char *entry, int *value,
                        unsigned int nentries) const;

        /**
         * Retreive an boolean value from the document.
         * @param entry The key of the value being searched for.
         * @param value The value to be returned.
         * @return True if the value is found, otherwise, false.
         */
        bool get_bool(const char *entry, bool &value) const;

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
         * @param nenetries The number of maximum number of entries the array
         * can hold is passed in.
         * @return The number of array entries found on success or -1 on
         * failure.
         */
        int get_doubles(const char *entry, double *value,
                        unsigned int nentries) const;

        Document m_doc;

      private:
        bool m_valid;
    };
}

#endif // _RAPIDJSON_JSON_DOCUMENT_HPP_
