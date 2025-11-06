// SPDX-License-Identifier: MIT
pragma solidity ^0.8.0;

contract ArtMarketplace {
    struct Artwork {
        uint256 id;
        string title;
        string artistName;
        address payable originalArtist;
        address payable currentOwner;
        uint256 price;
        bool listed;
    }

    uint256 public nextId;
    mapping(uint256 => Artwork) public artworks;

    event ArtworkListed(uint256 id, string title, string artistName, uint256 price);
    event ArtworkPurchased(
        uint256 id,
        address indexed seller,
        address indexed buyer,
        uint256 price,
        uint256 royaltyPaid
    );

    /**
     * @dev List a new artwork on the marketplace
     */
    function listArtwork(
        string memory _title,
        string memory _artistName,
        uint256 _price
    ) public {
        require(_price > 0, "Price must be greater than zero");

        artworks[nextId] = Artwork({
            id: nextId,
            title: _title,
            artistName: _artistName,
            originalArtist: payable(msg.sender),
            currentOwner: payable(msg.sender),
            price: _price,
            listed: true
        });

        emit ArtworkListed(nextId, _title, _artistName, _price);
        nextId++;
    }

    /**
     * @dev Allow current owner to re-list their artwork for resale
     */
    function relistArtwork(uint256 _id, uint256 _price) public {
        Artwork storage art = artworks[_id];
        require(msg.sender == art.currentOwner, "Only owner can relist");
        require(_price > 0, "Invalid price");

        art.price = _price;
        art.listed = true;

        emit ArtworkListed(_id, art.title, art.artistName, _price);
    }

    /**
     * @dev Purchase an artwork — includes 10% royalty to original artist on resales
     */
    function buyArtwork(uint256 _id) public payable {
        Artwork storage art = artworks[_id];
        require(art.listed, "Artwork not listed for sale");
        require(msg.sender != art.currentOwner, "Owner cannot buy own artwork");
        require(msg.value == art.price, "Incorrect payment amount");

        uint256 royalty = 0;
        uint256 sellerAmount = msg.value;

        // Apply royalty if not first sale
        if (art.originalArtist != art.currentOwner) {
            royalty = (msg.value * 10) / 100; // 10% royalty
            sellerAmount = msg.value - royalty;
            art.originalArtist.transfer(royalty);
        }

        address payable seller = art.currentOwner;
        art.currentOwner = payable(msg.sender);
        art.listed = false;

        seller.transfer(sellerAmount);

        emit ArtworkPurchased(_id, seller, msg.sender, art.price, royalty);
    }

    function getArtwork(uint256 _id)
        public
        view
        returns (
            uint256 id,
            string memory title,
            string memory artistName,
            address originalArtist,
            address currentOwner,
            uint256 price,
            bool listed
        )
    {
        Artwork memory art = artworks[_id];
        return (
            art.id,
            art.title,
            art.artistName,
            art.originalArtist,
            art.currentOwner,
            art.price,
            art.listed
        );
    }
}
