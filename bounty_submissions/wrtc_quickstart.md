# wRTC Quickstart Guide

A step-by-step guide to obtaining, verifying, and using wRTC (wrapped RustChain Credits) on Solana.

---

## What is wRTC?

wRTC is the Solana SPL token representation of RustChain Credits (RTC). It allows you to:
- Trade RTC on Solana DEXs like Raydium
- Bridge wRTC to BoTTube for platform credits
- Withdraw BoTTube credits back to wRTC

## Token Details

| Property | Value |
|----------|-------|
| **Name** | Wrapped RTC |
| **Symbol** | wRTC |
| **Mint Address** | `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X` |
| **Decimals** | 6 |
| **Chain** | Solana (SPL) |
| **Swap** | [Raydium](https://raydium.io/swap/?inputMint=sol&outputMint=12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X) |

---

## ⚠️ Anti-Scam Checklist

**Always verify before swapping:**

- [ ] Mint address matches exactly: `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X`
- [ ] Decimals are 6
- [ ] You're on the official Raydium link (raydium.io)
- [ ] The token has trading volume and liquidity
- [ ] Double-check the contract address in your wallet before confirming

**Never trust ticker-only matches.** Scammers create fake tokens with the same symbol. Always verify the mint address.

---

## How to Buy wRTC

### Method 1: Swap SOL for wRTC on Raydium

1. **Open Raydium Swap**
   - Go to: https://raydium.io/swap/
   - Or use direct link: [SOL → wRTC](https://raydium.io/swap/?inputMint=sol&outputMint=12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X)

2. **Connect Your Wallet**
   - Click "Connect Wallet"
   - Select your wallet (Phantom, Solflare, etc.)
   - Approve the connection

3. **Verify the Token**
   - Input: SOL
   - Output: Search for "wRTC"
   - **CRITICAL:** Click the token to verify the mint address matches `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X`

4. **Enter Amount**
   - Input how much SOL you want to swap
   - Review the estimated wRTC you'll receive
   - Check the price impact (aim for <5%)

5. **Confirm Swap**
   - Click "Swap"
   - Confirm in your wallet
   - Wait for transaction confirmation

6. **Verify Receipt**
   - Check your wallet for wRTC balance
   - Token should appear automatically (if not, add manually using the mint address)

### Method 2: Receive wRTC from Another Wallet

If someone is sending you wRTC, give them:
- Your Solana wallet address
- Tell them to use the mint: `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X`

---

## How to Verify Your wRTC

### Check in Phantom Wallet

1. Open Phantom
2. Look for wRTC in your token list
3. Click on wRTC
4. Verify:
   - Mint: `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X`
   - Decimals: 6

### Check on Solscan

1. Go to https://solscan.io
2. Paste your wallet address
3. Look for wRTC in the token list
4. Click the token name
5. Verify the mint address matches exactly

---

## How to Bridge wRTC to BoTTube Credits

Bridge URL: https://bottube.ai/bridge/wrtc

### Bridging wRTC → BoTTube Credits

1. **Go to the Bridge**
   - Visit https://bottube.ai/bridge/wrtc
   - Connect your Solana wallet

2. **Select Direction**
   - Choose "wRTC → BoTTube Credits"

3. **Enter Amount**
   - Input how much wRTC to bridge
   - Review the exchange rate (1:1)

4. **Confirm**
   - Click "Bridge"
   - Approve the transaction in your wallet
   - Wait for confirmation (~30 seconds)

5. **Verify**
   - Check your BoTTube account balance
   - Credits should appear immediately

### Withdrawing BoTTube Credits → wRTC

1. **Go to the Bridge**
   - Visit https://bottube.ai/bridge/wrtc
   - Make sure you're logged into BoTTube

2. **Select Direction**
   - Choose "BoTTube Credits → wRTC"

3. **Enter Amount**
   - Input how many credits to withdraw
   - Review any fees

4. **Confirm**
   - Click "Withdraw"
   - Confirm the transaction
   - wRTC will arrive in your wallet

---

## Using BoTTube Credits

Once you have BoTTube credits, you can:
- Tip content creators
- Subscribe to premium channels
- Purchase platform features

---

## Troubleshooting

### Token Not Showing in Wallet

**Solution:** Add the token manually
- Mint: `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X`
- Symbol: wRTC
- Decimals: 6

### Transaction Failed

**Check:**
- Do you have enough SOL for gas fees?
- Is the slippage tolerance high enough? (Try 1-2%)
- Is the liquidity pool active?

### Bridge Transaction Stuck

- Wait 2-3 minutes for confirmation
- Check your wallet transaction history
- Contact BoTTube support if stuck >10 minutes

---

## Quick Reference

| Resource | Link |
|----------|------|
| Raydium Swap | https://raydium.io/swap/?inputMint=sol&outputMint=12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X |
| BoTTube Bridge | https://bottube.ai/bridge/wrtc |
| Mint Address | `12TAdKXxcGf6oCv4rqDz2NkgxjyHq6HQKoxKZYGf5i4X` |

---

## Need Help?

- **BoTTube:** https://bottube.ai/support
- **RustChain Discord:** [Link in main README]
- **Raydium Docs:** https://docs.raydium.io/

---

*Last updated: February 2026*
