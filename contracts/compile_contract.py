import json
from solcx import compile_standard, install_solc

print("🧩 Installing Solidity compiler...")
install_solc('0.8.0')

with open("contracts/ArtMarketplace.sol", "r") as file:
    contract_source = file.read()

compiled_sol = compile_standard(
    {
        "language": "Solidity",
        "sources": {"ArtMarketplace.sol": {"content": contract_source}},
        "settings": {
            "outputSelection": {"*": {"*": ["abi", "metadata", "evm.bytecode", "evm.sourceMap"]}}
        },
    },
    solc_version="0.8.0",
)

with open("contracts/build/ArtMarketplace.json", "w") as f:
    json.dump(compiled_sol, f)

print("✅ Contract compiled successfully and saved in /contracts/build/")
