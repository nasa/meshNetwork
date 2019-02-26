/**
 * \file
 * Functions and types for CRC checks.
 *
 * Generated on Fri Feb 22 08:47:37 2019
 * by pycrc v0.9.2, https://pycrc.org
 * using the configuration:
 *  - Width         = 8
 *  - Poly          = 0x07
 *  - XorIn         = 0x00
 *  - ReflectIn     = False
 *  - XorOut        = 0x00
 *  - ReflectOut    = False
 *  - Algorithm     = table-driven
 *
 * This file defines the functions crc8_init(), crc8_update() and crc8_finalize().
 *
 * The crc8_init() function returns the inital \c crc value and must be called
 * before the first call to crc8_update().
 * Similarly, the crc8_finalize() function must be called after the last call
 * to crc8_update(), before the \c crc is being used.
 * is being used.
 *
 * The crc8_update() function can be called any number of times (including zero
 * times) in between the crc8_init() and crc8_finalize() calls.
 *
 * This pseudo-code shows an example usage of the API:
 * \code{.c}
 * crc8_t crc;
 * unsigned char data[MAX_DATA_LEN];
 * size_t data_len;
 *
 * crc = crc8_init();
 * while ((data_len = read_data(data, MAX_DATA_LEN)) > 0) {
 *     crc = crc8_update(crc, data, data_len);
 * }
 * crc = crc8_finalize(crc);
 * \endcode
 */
#ifndef CRC8_H
#define CRC8_H

#include <stdlib.h>
#include <stdint.h>
#include <vector>

#ifdef __cplusplus
extern "C" {
#endif


/**
 * The definition of the used algorithm.
 *
 * This is not used anywhere in the generated code, but it may be used by the
 * application code to call algorithm-specific code, if desired.
 */
#define CRC_ALGO_TABLE_DRIVEN 1


/**
 * The type of the CRC values.
 *
 * This type must be big enough to contain at least 8 bits.
 */
typedef uint_fast8_t crc8_t;


/**
 * Calculate the initial crc value.
 *
 * \return     The initial crc value.
 */
static inline crc8_t crc8_init(void)
{
    return 0x00;
}


/**
 * Update the crc value with new data.
 *
 * \param[in] crc      The current crc value.
 * \param[in] data     Pointer to a buffer of \a data_len bytes.
 * \param[in] data_len Number of bytes in the \a data buffer.
 * \return             The updated crc value.
 */
crc8_t crc8_update(crc8_t crc, std::vector<uint8_t> & data);


/**
 * Calculate the final crc value.
 *
 * \param[in] crc  The current crc value.
 * \return     The final crc value.
 */
static inline crc8_t crc8_finalize(crc8_t crc)
{
    return crc;
}

crc8_t crc8_create(std::vector<uint8_t> & data);

#ifdef __cplusplus
}           /* closing brace for extern "C" */
#endif

#endif      /* CRC8_H */
