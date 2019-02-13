#!/usr/bin/env python3
# Copyright (c) 2016-2017 The Bitcoin Core developers
# Copyright (c) 2018-2019 The Kevacoin Core developers
# Distributed under the MIT software license, see the accompanying
# file COPYING or http://www.opensource.org/licenses/mit-license.php.
"""Test the Key-Value Store."""

from test_framework.blocktools import witness_script, send_to_witness
from test_framework.test_framework import BitcoinTestFramework
from test_framework.util import *
from test_framework.authproxy import JSONRPCException
from io import BytesIO
import re


class KevaTest(BitcoinTestFramework):
    def set_test_params(self):
        self.setup_clean_chain = True
        self.num_nodes = 3

    def setup_network(self):
        super().setup_network()
        connect_nodes(self.nodes[0], 2)
        self.sync_all()

    def run_test(self):
        self.nodes[0].generate(161) #block 161
        response = self.nodes[0].keva_namespace('first_namespace')
        namespaceId = response['namespaceId']

        self.log.info("Test basic put and get operations")
        key = 'First Key'
        value = 'This is the first value!'
        self.nodes[0].keva_put(namespaceId, key, value)
        response = self.nodes[0].keva_pending()
        assert(response[0]['op'] == 'keva_namespace')
        assert(response[1]['op'] == 'keva_put')
        response = self.nodes[0].keva_get(namespaceId, key)
        assert(response['value'] == value)

        self.nodes[0].generate(1)
        response = self.nodes[0].keva_pending()
        assert(len(response) == 0)

        self.log.info("Test batch of put operations without exceeding the mempool chain limit")
        prefix = 'first-set-of-keys-'
        for i in range(24):
            key = prefix + str(i)
            value = ('value-' + str(i) + '-') * 300
            self.nodes[0].keva_put(namespaceId, key, value)

        response = self.nodes[0].keva_pending()
        assert(len(response) == 24)

        self.nodes[0].generate(1)
        response = self.nodes[0].keva_pending()
        assert(len(response) == 0)

        # This will throw "too-long-mempool-chain" exception
        self.log.info("Test batch of put operations that exceeds the mempool chain limit")
        throwException = False
        secondPrefix = 'second-set-of-keys-'
        try:
            for i in range(30):
                key = secondPrefix + '|' + str(i)
                value = '-value-' * 320 + '|' + str(i)
                self.nodes[0].keva_put(namespaceId, key, value)
        except JSONRPCException:
            throwException = True

        assert(throwException)

        self.nodes[0].generate(1)
        response = self.nodes[0].keva_pending()
        assert(len(response) == 0)

        self.log.info("Verify keva_filter works properly")
        response = self.nodes[0].keva_filter(namespaceId, secondPrefix)
        assert(len(response) == 25)

        for i in range(25):
            m = re.search('\|(\d+)', response[i]['key'])
            keyId = m.group(0)
            m = re.search('\|(\d+)', response[i]['value'])
            valueId = m.group(0)
            assert(keyId == valueId)

        self.log.info("Test keva_delete")
        keyToDelete = secondPrefix + '|13'
        self.nodes[0].keva_delete(namespaceId, keyToDelete)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, keyToDelete)
        assert(response['value'] == '')

        self.log.info("Test reset the value after deleting")
        newValue = 'This is the new value'
        self.nodes[0].keva_put(namespaceId, keyToDelete, newValue)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, keyToDelete)
        assert(response['value'] == newValue)

if __name__ == '__main__':
    KevaTest().main()
