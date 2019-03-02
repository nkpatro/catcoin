#include <cmath>
#include <stdint.h>
#include <string>
#include <algorithm>
#include "cryptonote_core/cryptonote_basic.h"
#include "cryptonote_core/cryptonote_format_utils.h"
#include "cryptonote_protocol/blobdatatype.h"
#include "crypto/crypto.h"
#include "crypto/hash.h"
#include "common/base58.h"
#include "serialization/binary_utils.h"


uint32_t convert_blob(const char *blob, size_t len, char *out) {
    std::string input = std::string(blob, len);
    cryptonote::blobdata output = "";

    cryptonote::block b = AUTO_VAL_INIT(b);
    if (!cryptonote::parse_and_validate_block_from_blob(input, b)) {
        return 0;
    }

    if (!cryptonote::get_block_hashing_blob(b, output)) {
        return 0;
    }

    output.copy(out, output.length(), 0);
    return output.length();
}

bool validate_address(const char *addr, size_t len) {
    std::string input = std::string(addr, len);
    std::string output = "";
    uint64_t prefix;
    return tools::base58::decode_addr(addr, prefix, output);
}