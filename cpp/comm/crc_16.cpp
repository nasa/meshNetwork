#include "comm/crc_16.hpp" 
#include <stdio.h>

using std::vector;

namespace comm {

/**
 * Reflect all bits of a \a data word of \a data_len bytes.
 *
 * \param data         The data word to be reflected.
 * \param data_len     The width of \a data expressed in number of bits.
 * \return             The reflected data.
 *****************************************************************************/
crc16_t crc16_reflect(crc16_t data, size_t data_len)
{
    unsigned int i;
    crc16_t ret;

    ret = data & 0x01;
    for (i = 1; i < data_len; i++) {
        data >>= 1;
        ret = (ret << 1) | (data & 0x01);
    }
    return ret;
}


/**
 * Update the crc value with new data.
 *
 * \param crc      The current crc value.
 * \param data     Pointer to a buffer of \a data_len bytes.
 * \param data_len Number of bytes in the \a data buffer.
 * \return         The updated crc value.
 *****************************************************************************/
crc16_t crc16_update(crc16_t crc, vector<uint8_t> & data)
{
    unsigned int tbl_idx;

    for (unsigned int i = 0; i < data.size(); i++) {
        tbl_idx = (crc ^ data[i]) & 0xff;
        crc = (crc16_table[tbl_idx] ^ (crc >> 8)) & 0xffff;
    }
    return crc & 0xffff;
}

crc16_t crc16_create(vector<uint8_t> & data) {
    crc16_t crc;
    crc = crc16_init();
    crc = crc16_update(crc, data);
    crc = crc16_finalize(crc);

    return crc;
}
/*
crc16_t bytesToCrc(vector<uint8_t> & bytes, unsigned int pos) {
    return (uint16_t)(bytes[pos] | (bytes[pos+1] << 8));
}

vector<uint8_t> crcToBytes(crc16_t crc) {
    vector<uint8_t> crcBytes;
    crcToBytes(crcBytes, crc);
    return crcBytes;
}

void crcToBytes(vector<uint8_t> & output, crc16_t crc) {
    output.push_back((uint8_t)(crc & 0x00FF));
    output.push_back((uint8_t)(crc >> 8));

}*/

}


