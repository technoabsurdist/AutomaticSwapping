import json 
from web3 import Web3, EthereumTesterProvider
from time import sleep
from dotenv import load_dotenv
from constants import ETH_KEY, my_address, t_path, u_path, t_addr, u_addr

load_dotenv()
w3 = Web3(EthereumTesterProvider())

def get_abi(path, address):
    with open(path, 'r') as f:
        abi = json.load(f)
    abi = w3.eth.contract(address=address, abi=abi)
    return abi

def connect_to_eth():
    return w3.is_connected(), w3

def wait_for_receipt(w3, tx_hash):
    while True:
        tx_receipt = w3.eth.getTransactionReceipt(tx_hash)
        if tx_receipt:
            return tx_receipt
        sleep(1)

def main():
    connected, w3 = connect_to_eth()
    while not connected:
        sleep(5)
        connected, w3 = connect_to_eth()
    
    print("ETP connected")
    

    # GET tether + uniswap abi
    tether_abi = get_abi(t_path, t_addr)
    tether_contract = w3.eth.contract(address=t_addr, abi=tether_abi)

    uniswap_abi = get_abi(u_path, u_addr)
    uniswap_contract = w3.eth.contract(address=u_addr, abi=uniswap_abi)

    tether_balance = tether_contract.functions.balanceOf(my_address).call()

    if tether_balance == 0:
        print("No Tether balance, exiting.")
        return -1

    eth_balance = w3.eth.getBalance(my_address)
    gas_price = w3.eth.generate_gas_price()

    if eth_balance < gas_price:
        print("Not enough balance for gas, exiting.")
        return -1


    approve_txn = tether_contract.functions.approve(
        u_addr,
        tether_balance      
    ).buildTransaction({
        'from': my_address,
        'gas': 50000,
        'gasPrice': gas_price
    })
    signed_approve_txn = w3.eth.account.signTransaction(approve_txn, my_address)
    approve_tx_hash = w3.eth.sendRawTransaction(signed_approve_txn.rawTransaction)
    
    wait_for_receipt(w3, approve_tx_hash)

    amount_in = tether_balance

    path = [t_addr, w3.toChecksumAddress(my_address)]      
    deadline = w3.eth.getBlock('latest')['timestamp'] + 120      
    swap_txn = uniswap_contract.functions.swapExactTokensForETH(
        amount_in,
        # 0,
        path,
        my_address,
        deadline
    ).buildTransaction({
        'from': my_address,
        'gas': 50000,
        'gasPrice': gas_price
    })
    
    signed_swap_txn = w3.eth.account.signTransaction(swap_txn, ETH_KEY)
    swap_tx_hash = w3.eth.sendRawTransaction(signed_swap_txn.rawTransaction)
    
    # Wait for swap to be mined
    wait_for_receipt(w3, swap_tx_hash)
 
    
    print(f"Swapped {amount_in} Tether for ETH. Transaction Hash: {swap_tx_hash.hex()}")




if __name__ == '__main__':
    main()

