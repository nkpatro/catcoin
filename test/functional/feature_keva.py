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
        self.num_nodes = 2

    def setup_network(self):
        super().setup_network()
        connect_nodes_bi(self.nodes, 0, 1)
        self.sync_all()

    def run_unconfirmed_namespaces(self):
        self.sync_all()
        response = self.nodes[1].keva_namespace('second_namespace')
        namespaceId = response['namespaceId']
        response = self.nodes[1].keva_list_namespaces()
        # Node 0's unconfirmed namespace should not be here
        assert(len(response) == 1)

        # Node 0's unconfirmed operations should not be here
        self.nodes[1].keva_put(namespaceId, 'second_key', 'second_value')
        response = self.nodes[1].keva_pending()
        # Pending namespace and put operation.
        assert(len(response) == 2)
        self.sync_all()

    def run_test_disconnect_block(self):
        displayName = 'namespace_to_test'
        response = self.nodes[0].keva_namespace(displayName)
        namespaceId = response['namespaceId']
        self.nodes[0].generate(1)

        key = 'This is the test key'
        value1 = 'This is the test value 1'
        value2 = 'This is the test value 1'
        self.nodes[0].keva_put(namespaceId, key, value1)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, key)
        assert(response['value'] == value1)
        self.nodes[0].keva_put(namespaceId, key, value2)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, key)
        assert(response['value'] == value2)
        # Disconnect the block
        self.sync_all()
        self.nodes[0].invalidateblock(self.nodes[0].getbestblockhash())
        self.nodes[1].invalidateblock(self.nodes[1].getbestblockhash())
        self.sync_all()
        response = self.nodes[0].keva_get(namespaceId, key)
        assert(response['value'] == value1)
        # Disconnect the block again
        self.sync_all()
        self.nodes[0].invalidateblock(self.nodes[0].getbestblockhash())
        self.nodes[1].invalidateblock(self.nodes[1].getbestblockhash())
        self.sync_all()
        response = self.nodes[0].keva_get(namespaceId, key)
        assert(response['value'] == '')
        response = self.nodes[0].keva_get(namespaceId, '_KEVA_NS_')
        assert(response['value'] == displayName)

        self.log.info("Test undeleting after disconnecting blocks")
        self.nodes[0].generate(1)
        keyToDelete = 'This is the test key to delete'
        valueToDelete = 'This is the test value of the key'
        self.nodes[0].keva_put(namespaceId, keyToDelete, valueToDelete)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, keyToDelete)
        assert(response['value'] == valueToDelete)
        # Now delete the key
        self.nodes[0].keva_delete(namespaceId, keyToDelete)
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_get(namespaceId, keyToDelete)
        assert(response['value'] == '')
        # Disconnect the block
        self.sync_all()
        self.nodes[0].invalidateblock(self.nodes[0].getbestblockhash())
        self.nodes[1].invalidateblock(self.nodes[1].getbestblockhash())
        self.sync_all()
        response = self.nodes[0].keva_get(namespaceId, keyToDelete)
        # The value should be undeleted.
        assert(response['value'] == valueToDelete)

        self.log.info("Test namespace after disconnecting blocks")
        displayName = 'A new namspace'
        response = self.nodes[0].keva_namespace(displayName)
        newNamespaceId = response['namespaceId']
        self.nodes[0].generate(1)
        response = self.nodes[0].keva_list_namespaces()
        found = False
        for ns in response:
            if (ns['namespaceId'] == newNamespaceId):
                found = True
        assert(found)
        # Now disconnect the block and the namespace should be gone.
        self.sync_all()
        self.nodes[0].invalidateblock(self.nodes[0].getbestblockhash())
        self.nodes[1].invalidateblock(self.nodes[1].getbestblockhash())
        self.sync_all()
        # The namespace display name should not be set.
        response = self.nodes[0].keva_get(newNamespaceId, '_KEVA_NS_')
        assert(response['value'] == '')
        # The namespace should not appear in the result of keva_list_namespaces
        response = self.nodes[0].keva_list_namespaces()
        found = False
        for ns in response:
            if (ns['namespaceId'] == newNamespaceId):
                found = True
        assert(not found)


    def run_test(self):
        self.nodes[0].generate(105)
        self.nodes[1].generate(105)
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

        self.log.info("Test other wallet's unconfirmed namespaces do not show up in ours")
        self.run_unconfirmed_namespaces()

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
        except JSONRPCException as e:
            if str(e).find("too-long-mempool-chain") >= 0:
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

        self.log.info("Test disconnecting blocks")
        self.run_test_disconnect_block()


if __name__ == '__main__':
    KevaTest().main()
