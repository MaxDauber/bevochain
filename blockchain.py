import hashlib
import json
from time import time
from uuid import uuid4

from flask import Flask, jsonify, request

""" 
The Blockchain class manages the chain. It stores transaction methods
and has methods for adding blocks to the chain.
"""


class Blockchain(object):
    def __init__(self):
        self.chain = []
        self.current_transactions = []

        # Create genesis block
        self.create_block(previous_hash=1, proof=100)

    def create_block(self, proof, previous_hash=None):
        """
        Create a new Block in the Blockchain, add it to chain

        :param proof: <int> proof given by Proof of Work algorithm
        :param previous_hash: <str> Hash of previous Block
        :return: <dict> new Block
        """

        block = {
            'index': len(self.chain) + 1,
            'timestamp': time(),
            'transactions': self.current_transactions,
            'proof': proof,
            'previous_hash': previous_hash,
        }

        # Reset current list of transactions
        self.current_transactions = []

        self.chain.append(block)
        return block

    def create_transaction(self, sender, recipient, amount):
        """
        Create new transaction to go into next mined Block

        :param sender: <str> sender address
        :param recipient: <str> recipient address
        :param amount: <int> transaction amount
        :return: <int> index of Block that will hold transaction
        """

        self.current_transactions.append({
            'sender': sender,
            'recipient': recipient,
            'amount': amount,
        })
        return self.last_block['index'] + 1

    @staticmethod
    # Hashes a block
    def hash(block):
        """
        Creates SHA-256 hash of Block

        :param block: <dict> Block
        :return: <str>
        """

        # Dictionary must be ordered, else hashes will be inconsistent
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    # Return last block in chain
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        """
        Proof of Work Algorithm:
            - Find number num' such that hash(num') has 2 leading
              zeroes
            - num is previous proof, num' is new proof

        :param last_proof: <int>
        :return: <int>
        """
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1

        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        """
        Validates proof, checks if hash(last_proof, proof) has 2
        leading zeroes

        :param last_proof: <int> previous Proof
        :param proof: <int> current Proof
        :return: <bool> correct returns True, incorrect returns False
        """

        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:2] == "00"


# Instantiate node
app = Flask(__name__)

# Randomly create a global unique address for the node
node_identifier = str(uuid4()).replace('-', '')

# Instantiate Blockchain class
blockchain = Blockchain()


# Create /mine endpoint, is GET request
@app.route('/mine', methods=['GET'])
def mine():
    # Run algorithm to receive next Proof of Work
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)

    # Receive reward for finding proof
    # Sender is "0" to show node has mined new coin
    blockchain.create_transaction(
        sender="0",
        recipient=node_identifier,
        amount=1,
    )

    # Forge new Block by adding it to chain
    previous_hash = blockchain.hash(last_block)
    block = blockchain.create_block(proof, previous_hash)

    response = {
        'message': "New Block Forged",
        'index': block['index'],
        'transactions': block['transactions'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash'],
    }
    return jsonify(response), 200


# Create /transactions/new endpoint, is POST request
@app.route('/transactions/new', methods=['POST'])
def create_transaction():
    values = request.get_json()

    # Check required fields are in POST data
    required = ['sender', 'recipient', 'amount']
    if not all(k in values for k in required):
        return 'Missing values', 400

    # Create new transaction
    index = blockchain.create_transaction(values['sender'], values['recipient'], values['amount'])

    response = {'message': f'Transaction will be added to Block {index}'}
    return jsonify(response), 201


# Create /chain endpoint, returns full Blockchain, is GET request
@app.route('/chain', methods=['GET'])
def full_chain():
    response = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
    }
    return jsonify(response), 200


# Runs server on port 5000
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
