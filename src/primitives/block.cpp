// Copyright (c) 2009-2010 Satoshi Nakamoto
// Copyright (c) 2009-2017 The Bitcoin Core developers
// Distributed under the MIT software license, see the accompanying
// file COPYING or http://www.opensource.org/licenses/mit-license.php.

#include <arith_uint256.h>
#include <primitives/block.h>
#include <streams.h>

#include <hash.h>
#include <tinyformat.h>
#include <utilstrencodings.h>
#include <crypto/common.h>
#include <validation.h>
#include <crypto/hash-ops.h>

extern "C" void cn_slow_hash(const void *data, size_t length, char *hash, int variant, int prehashed, uint64_t height);
extern "C" void cn_fast_hash(const void *data, size_t length, char *hash);

namespace
{
    boost::mutex max_concurrency_lock;
    unsigned max_concurrency = boost::thread::hardware_concurrency();
}

void set_max_concurrency(unsigned n)
{
    if (n < 1)
        n = boost::thread::hardware_concurrency();
    unsigned hwc = boost::thread::hardware_concurrency();
    if (n > hwc)
        n = hwc;
    boost::lock_guard<boost::mutex> lock(max_concurrency_lock);
    max_concurrency = n;
}

unsigned get_max_concurrency()
{
    boost::lock_guard<boost::mutex> lock(max_concurrency_lock);
    return max_concurrency;
}

static uint256 cn_get_block_hash_by_height(uint64_t seed_height, char cnHash[32])
{
    CBlockIndex* pblockindex = chainActive[seed_height];
    uint256 blockHash = pblockindex->GetBlockHash();
    const unsigned char* pHash = blockHash.begin();
    for (int j = 31; j >= 0; j--) {
        cnHash[31 - j] = pHash[j];
    }
}

uint256 CBlockHeader::GetOriginalBlockHash() const
{
    CHashWriter hashWriter(SER_GETHASH, PROTOCOL_VERSION);
    hashWriter.write(BEGIN(nVersion), 80);
    return hashWriter.GetHash();
}

// prev_id of CN header is used to store the kevacoin block hash.
// The value of prev_id and block hash must be the same to prove
// that PoW has been properly done.
bool CBlockHeader::isCNConsistent() const
{
    return (GetOriginalBlockHash() == cnHeader.prev_id);
}

uint256 CBlockHeader::GetHash() const
{
    uint256 thash;
    if (!isCNConsistent()) {
        memset(thash.begin(), 0xff, thash.size());
        return thash;
    }
    cryptonote::blobdata blob = cryptonote::t_serializable_object_to_blob(cnHeader);
    cn_fast_hash(blob.data(), blob.size(), BEGIN(thash));
    return thash;
}

uint256 CBlockHeader::GetPoWHash() const
{
    uint256 thash;
    if (!isCNConsistent()) {
        memset(thash.begin(), 0xff, thash.size());
        return thash;
    }
    cryptonote::blobdata blob = cryptonote::t_serializable_object_to_blob(cnHeader);
    uint32_t height = nNonce;
    if (cnHeader.major_version >= RX_BLOCK_VERSION) {
        uint64_t seed_height;
        char cnHash[32];
        seed_height = crypto::rx_seedheight(height);
        cn_get_block_hash_by_height(seed_height, cnHash);
        crypto::rx_slow_hash(height, seed_height, cnHash, blob.data(), blob.size(), BEGIN(thash), get_max_concurrency(), 0);
    } else {
        cn_slow_hash(blob.data(), blob.size(), BEGIN(thash), cnHeader.major_version - 6, 0, height);
    }
    return thash;
}

std::string CBlock::ToString() const
{
    std::stringstream s;
    s << strprintf("CBlock(hash=%s, ver=0x%08x, hashPrevBlock=%s, hashMerkleRoot=%s, nTime=%u, nBits=%08x, nNonce=%u, vtx=%u)\n",
        GetOriginalBlockHash().ToString(),
        nVersion,
        hashPrevBlock.ToString(),
        hashMerkleRoot.ToString(),
        nTime, nBits, nNonce,
        vtx.size());
    for (const auto& tx : vtx) {
        s << "  " << tx->ToString() << "\n";
    }
    return s.str();
}
