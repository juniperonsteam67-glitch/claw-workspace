#!/usr/bin/env python3
"""Monitor Claw's autonomous wallet for incoming transactions."""
import urllib.request
import urllib.error
import json
import time
from datetime import datetime

WALLET_ADDRESS = "0x1867c3293105155854Ae9373C5f555939F942A89"

def check_balance():
    """Check ETH balance on mainnet via public RPC."""
    try:
        mainnet_rpc = "https://eth.llamarpc.com"
        payload = {
            "jsonrpc": "2.0",
            "method": "eth_getBalance",
            "params": [WALLET_ADDRESS, "latest"],
            "id": 1
        }
        data = json.dumps(payload).encode('utf-8')
        req = urllib.request.Request(
            mainnet_rpc,
            data=data,
            headers={'Content-Type': 'application/json'},
            method='POST'
        )
        with urllib.request.urlopen(req, timeout=10) as resp:
            result = json.loads(resp.read().decode('utf-8'))
            if 'result' in result:
                wei = int(result['result'], 16)
                eth = wei / 1e18
                return eth
    except Exception as e:
        print(f"Error: {e}")
    return None

def log_status():
    """Log current status to file."""
    now = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    balance = check_balance()
    
    status = {
        "timestamp": now,
        "wallet": WALLET_ADDRESS,
        "balance_eth": balance,
        "status": "active" if balance is not None else "error"
    }
    
    with open("/config/clawd/wallet_monitor.jsonl", "a") as f:
        f.write(json.dumps(status) + "\n")
    
    return balance

if __name__ == "__main__":
    print(f"🔍 Monitoring wallet: {WALLET_ADDRESS}")
    bal = log_status()
    if bal is not None:
        print(f"💰 Balance: {bal:.6f} ETH")
        if bal > 0:
            print("🎉 WALLET HAS FUNDS!")
    else:
        print("⚠️ Could not fetch balance")
