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

extern "C" void cn_slow_hash(const void *data, size_t length, char *hash, int variant, int prehashed, uint64_t height);

uint256 CBlockHeader::GetHash() const
{
    CHashWriter hashWriter(SER_GETHASH, PROTOCOL_VERSION);
    hashWriter.write(BEGIN(nVersion), 80);
    return hashWriter.GetHash();
}

uint256 CBlockHeader::GetPoWHash() const
{
    uint256 thash;
    if (hashPrevBlock.IsNull()) {
        // Genesis block
        cn_slow_hash(BEGIN(nVersion), 80, BEGIN(thash), 2, 0, 0);
        return thash;
    }
    arith_uint256 blockHash = UintToArith256(GetHash());
    arith_uint256 expectedHash = UintToArith256(cnHeader.prev_id);
    // blockHash should be the same as expectedHash. If so, after the
    // following XOR operatiosn, the value of expectedHash is not changed.
    blockHash ^= expectedHash;
    expectedHash ^= blockHash;
    CryptoNoteHeader cnHeaderCompute = cnHeader;
    // Cryptonote prev_id is used to store kevacoin block hash.
    cnHeaderCompute.prev_id = ArithToUint256(expectedHash);
    cryptonote::blobdata blob = cryptonote::t_serializable_object_to_blob(cnHeaderCompute);
    cn_slow_hash(blob.data(), blob.size(), BEGIN(thash), 2, 0, 0);
    return thash;
}

std::string CBlock::ToString() const
{
    std::stringstream s;
    s << strprintf("CBlock(hash=%s, ver=0x%08x, hashPrevBlock=%s, hashMerkleRoot=%s, nTime=%u, nBits=%08x, nNonce=%u, vtx=%u)\n",
        GetHash().ToString(),
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
