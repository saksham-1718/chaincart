// Navigation tab click: open related local page in same tab
document.querySelectorAll('nav a').forEach(el => {
    el.addEventListener('click', function(e) {
        e.preventDefault();
            // If the anchor already has an explicit href (local), honor it and navigate
            const explicitHref = el.getAttribute && el.getAttribute('href');
            if (explicitHref && explicitHref.trim() && explicitHref !== '#' && !explicitHref.startsWith('javascript:')){
                location.href = explicitHref;
                return;
            }
        const text = el.textContent.trim();
        let url = 'index.html';
        // match by visible text or icon presence
        if (text === 'Painting') url = 'painting.html';
        else if (text === 'Printmaking') url = 'printmaking.html';
        else if (text === 'Digital Art') url = 'digital-art.html';
        else if (text === 'Drawing') url = 'drawing.html';
        else if (text === 'Prints') url = 'prints.html';
        else if (text === 'Sculpture') url = 'sculpture.html';
        else if (text === 'Photography') url = 'photography.html';
        else if (text === 'Auction') url = 'auction.html';
        else if (text.startsWith('More')) url = 'more.html';
        // icons (cart/wallet/user)
        else if (el.querySelector('.fa-cart-shopping')) url = 'cart.html';
        else if (el.querySelector('.fa-wallet')) url = 'wallet.html';
        else if (el.querySelector('.fa-circle-user')) url = 'account.html';
        // navigate in the same tab
        location.href = url;
    });
});

// Default .btn behavior: do not hijack navigation. Only navigate if the element
// explicitly provides a href or a data-href. Skip buttons intended for JS actions.
document.querySelectorAll('.btn').forEach(el => {
    if (el.classList && el.classList.contains('add-to-cart')) return; // leave add-to-cart buttons for their own handler
    el.addEventListener('click', function(e) {
        // allow wallet-specific buttons to work normally
        if (el.closest && el.closest('.wallet-panel')) return;
        // If the element is an anchor with a meaningful href, allow default navigation
        const explicitHref = el.getAttribute && el.getAttribute('href');
        if (explicitHref && explicitHref.trim() && explicitHref !== '#' && !explicitHref.startsWith('javascript:')){
            return; // let the browser follow the href
        }
        // If a data-href is provided, navigate there
        const dataHref = el.dataset && el.dataset.href;
        if (dataHref && dataHref.trim()){
            e.preventDefault();
            location.href = dataHref;
        }
        // otherwise, don't force a redirect (previous behavior navigated to explore.html)
    });
});

// Newsletter button opens local newsletter page (if present)
const newsletterBtn = document.querySelector('.newsletter button');
if (newsletterBtn) {
    newsletterBtn.addEventListener('click', function(e) {
        e.preventDefault();
        location.href = 'newsletter.html';
    });
}

// Tab functionality for artists section (changes active tab visually and navigates locally)
const tabBtns = document.querySelectorAll('.tab-btn');
tabBtns.forEach(btn => {
    btn.addEventListener('click', function(e) {
        tabBtns.forEach(b => b.classList.remove('active'));
        this.classList.add('active');
        const tabText = btn.textContent.trim();
        let url = 'artists-all.html';
        if (tabText === 'Artist of the Week') url = 'artists-week.html';
        else if (tabText === 'Popular Artist') url = 'artists-popular.html';
        else if (tabText === 'Trending Artist') url = 'artists-trending.html';
        else if (tabText === 'Most Visited') url = 'artists-visited.html';
        else if (tabText === 'All Artists') url = 'artists-all.html';
        location.href = url;
    });
});

// Add some interactive animations (unchanged)
document.addEventListener('DOMContentLoaded', function() {
    // Animate elements on scroll
    const observerOptions = {
        threshold: 0.1,
        rootMargin: '0px 0px -50px 0px'
    };
    const observer = new IntersectionObserver(function(entries) {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                entry.target.style.opacity = 1;
                entry.target.style.transform = 'translateY(0)';
            }
        });
    }, observerOptions);
    // Observe elements to animate
    const elementsToAnimate = document.querySelectorAll('.artwork-card, .category-item, .artist-card');
    elementsToAnimate.forEach(el => {
        el.style.opacity = 0;
        el.style.transform = 'translateY(20px)';
        el.style.transition = 'opacity 0.5s ease, transform 0.5s ease';
        observer.observe(el);
    });
    // Wallet functionality
    const balanceEl = document.getElementById('wallet-balance');
    const connectBtn = document.getElementById('connect-wallet');
    const addBtn = document.getElementById('add-funds');
    const withdrawBtn = document.getElementById('withdraw-funds');
    const amountInput = document.getElementById('amount-input');
    const statusEl = document.getElementById('wallet-status');
    const txList = document.getElementById('tx-list');
    const clearTx = document.getElementById('clear-tx');

    // minimal wallet state persisted in localStorage
    const STORAGE_KEY = 'chaincart_wallet_v1';
    let state = { connected: false, balance: 0, tx: [] };

    function loadState(){
        try{
            const raw = localStorage.getItem(STORAGE_KEY);
            if(raw) state = JSON.parse(raw);
        }catch(e){ console.warn('wallet load err', e); }
    }
    function saveState(){
        try{ localStorage.setItem(STORAGE_KEY, JSON.stringify(state)); }catch(e){ console.warn('wallet save err', e); }
    }

    function render(){
        // format as Indian Rupees with symbol and INR label
        balanceEl.textContent = '₹ ' + state.balance.toFixed(2) + ' INR';
        statusEl.textContent = state.connected ? 'Connected' : 'Not connected';
        connectBtn.textContent = state.connected ? 'Disconnect' : 'Connect Wallet';
        // render tx
        txList.innerHTML = '';
        if(state.tx.length === 0){
            txList.innerHTML = '<li class="tx-item">No transactions yet</li>';
        } else {
            state.tx.slice().reverse().forEach(t => {
                const li = document.createElement('li');
                li.className = 'tx-item';
                li.innerHTML = `<span>${t.memo || ''}</span><span class="${t.type==='in' ? 'tx-type-in' : 'tx-type-out'}">₹ ${t.amount.toFixed(2)} INR</span>`;
                txList.appendChild(li);
            });
        }
    }

    function pushTx(type, amount, memo){
        state.tx.push({ type, amount: Number(amount), memo, at: Date.now() });
        // keep last 200
        if(state.tx.length > 200) state.tx = state.tx.slice(state.tx.length - 200);
        saveState();
        render();
    }

    // wire up
    loadState();
    render();

    // Product thumbnails: swap main image on click (applies on product pages)
    try{
        const mainImg = document.getElementById('MainImg');
        const thumbs = document.querySelectorAll('.small-img');
        if(mainImg && thumbs && thumbs.length){
                thumbs.forEach((thumb, idx) => {
                    thumb.addEventListener('click', function(){
                        // swap main image src to clicked thumbnail src
                        const newSrc = thumb.getAttribute('src');
                        if(newSrc){
                            mainImg.setAttribute('src', newSrc);
                            // set active class
                            thumbs.forEach(t => t.classList.remove('active'));
                            thumb.classList.add('active');
                        }
                    });
                    // keyboard support: Enter/Space to select, Left/Right to move focus
                    thumb.addEventListener('keydown', function(e){
                        if(e.key === 'Enter' || e.key === ' '){ e.preventDefault(); thumb.click(); }
                        else if(e.key === 'ArrowRight'){
                            e.preventDefault(); const next = thumbs[(idx+1) % thumbs.length]; next && next.focus();
                        } else if(e.key === 'ArrowLeft'){
                            e.preventDefault(); const prev = thumbs[(idx-1+thumbs.length) % thumbs.length]; prev && prev.focus();
                        }
                    });
                });
                // click main image to cycle to next thumbnail
                mainImg.addEventListener('click', function(){
                    try{
                        const activeIndex = Array.from(thumbs).findIndex(t => t.classList.contains('active'));
                        const nextIndex = (activeIndex < 0) ? 0 : ((activeIndex + 1) % thumbs.length);
                        const nextThumb = thumbs[nextIndex];
                        if(nextThumb){
                            nextThumb.click();
                            // make sure it's scrolled into view in the thumbnail strip
                            nextThumb.scrollIntoView({ behavior: 'smooth', inline: 'center' });
                        }
                    }catch(e){ console.warn('cycle main img failed', e); }
                });
        }
    }catch(e){ console.warn('thumb swap init failed', e); }

        // --- Cart functionality: persist cart in localStorage and bind Add to Cart button ---
        (function setupCart(){
            try{
                const CART_KEY = 'chaincart_cart_v1';
                function loadCart(){ try{ return JSON.parse(localStorage.getItem(CART_KEY)) || []; }catch(e){ return []; } }
                function saveCart(cart){ try{ localStorage.setItem(CART_KEY, JSON.stringify(cart)); }catch(e){} }
                function updateCartCount(){
                    const cart = loadCart();
                    const count = cart.reduce((s,i)=>s + (i.qty||0), 0);
                    let badge = document.getElementById('cart-count');
                    if(!badge){
                        const cartLink = document.querySelector('a[aria-label="Cart"], a[href*="cart"]');
                        if(cartLink){
                            badge = document.createElement('span');
                            badge.id = 'cart-count';
                            badge.className = 'cart-count-badge';
                            badge.textContent = count;
                            cartLink.appendChild(badge);
                        }
                    } else {
                        badge.textContent = count;
                    }
                }

                function showToast(msg){
                    const t = document.createElement('div');
                    t.className = 'cc-toast';
                    t.textContent = msg;
                    document.body.appendChild(t);
                    requestAnimationFrame(()=> t.classList.add('visible'));
                    setTimeout(()=>{ t.classList.remove('visible'); setTimeout(()=> t.remove(), 300); }, 1800);
                }

                function addToCartItem(item){
                    const cart = loadCart();
                    const idx = cart.findIndex(c => c.id === item.id);
                    if(idx >= 0){ cart[idx].qty = (cart[idx].qty || 1) + (item.qty || 1); }
                    else { cart.push(item); }
                    saveCart(cart);
                    updateCartCount();
                }

                // Bind Add to Cart button on product pages
                const addBtn = document.getElementById('sign-out-btn') || document.querySelector('.single-pro-details .btn.secondary');
                if(addBtn){
                    addBtn.addEventListener('click', function(e){
                        e.preventDefault();
                        const title = document.querySelector('.single-pro-details h4')?.textContent.trim() || document.title;
                        const artist = document.querySelector('.single-pro-details h6')?.textContent.trim() || '';
                        const priceText = document.querySelector('.single-pro-details h2')?.textContent.trim() || '';
                        const img = document.getElementById('MainImg')?.getAttribute('src') || '';
                        const productId = window.location.pathname + '::' + title;
                        const item = { id: productId, title, artist, price: priceText, img, qty: 1 };
                        addToCartItem(item);
                        showToast('Added to cart');
                    });
                }

                // Bind listing Add-to-Cart buttons (.add-to-cart) present on pages like painting.html
                const listAddBtns = document.querySelectorAll('.add-to-cart');
                if(listAddBtns && listAddBtns.length){
                    listAddBtns.forEach(btn => {
                        btn.addEventListener('click', function(e){
                            e.preventDefault();
                            const title = btn.getAttribute('data-title') || btn.closest('.artwork-card')?.querySelector('.artwork-title')?.textContent.trim() || document.title;
                            const artist = btn.getAttribute('data-artist') || btn.closest('.artwork-card')?.querySelector('.artwork-artist')?.textContent.trim() || '';
                            const priceText = btn.getAttribute('data-price') || btn.closest('.artwork-card')?.querySelector('.artwork-price')?.textContent.trim() || '';
                            const img = btn.getAttribute('data-img') || '';
                            const productId = btn.getAttribute('data-id') || (window.location.pathname + '::' + title + '::' + artist);
                            const item = { id: productId, title, artist, price: priceText, img, qty: 1 };
                            addToCartItem(item);
                            showToast('Added to cart');
                        });
                    });
                }

                // init count
                updateCartCount();
            }catch(e){ console.warn('cart setup failed', e); }
        })();

    // Create a tooltip element for header wallet icon (if present)
    (function setupHeaderWalletTooltip(){
        try{
            // robust selector: prefer any anchor with href containing 'wallet', else find an element with a wallet icon and get its closest anchor
            let walletLink = document.querySelector('a[href*="wallet"]');
            if(!walletLink){
                const icon = document.querySelector('.fa-wallet, .fa-solid.fa-wallet, i.fa-wallet, i.fas.fa-wallet');
                if(icon) walletLink = icon.closest('a');
            }
            if(!walletLink) return; // no wallet link on this page

            // create tooltip and append to body (only once)
            let tip = document.getElementById('wallet-tooltip');
            if(!tip){
                tip = document.createElement('div');
                tip.className = 'wallet-tooltip';
                tip.id = 'wallet-tooltip';
                document.body.appendChild(tip);
            }

            function updateTipText(){ tip.textContent = 'Balance: ₹ ' + (state && typeof state.balance === 'number' ? state.balance.toFixed(2) : '0.00') + ' INR'; }
            updateTipText();

            function positionTip(){
                const rect = walletLink.getBoundingClientRect();
                const tipRect = tip.getBoundingClientRect();
                // prefer above the link; if not enough space, position below
                const aboveTop = window.scrollY + rect.top - tipRect.height - 12;
                const belowTop = window.scrollY + rect.bottom + 12;
                const top = (aboveTop > window.scrollY + 8) ? aboveTop : belowTop;
                const left = window.scrollX + rect.left + (rect.width/2) - (tipRect.width/2);
                tip.style.top = top + 'px';
                tip.style.left = Math.max(8, left) + 'px';
            }

            let hoverTimeout;
            // show on mouseenter, hide on mouseleave
            walletLink.addEventListener('mouseenter', function(){
                updateTipText();
                tip.classList.add('visible');
                // position after it's visible so size measurements are correct
                requestAnimationFrame(positionTip);
                clearTimeout(hoverTimeout);
            });
            walletLink.addEventListener('mouseleave', function(){
                hoverTimeout = setTimeout(()=> tip.classList.remove('visible'), 80);
            });

            // update tooltip on resize/scroll
            window.addEventListener('resize', function(){ if(tip.classList.contains('visible')) positionTip(); });
            window.addEventListener('scroll', function(){ if(tip.classList.contains('visible')) positionTip(); });

            // update tooltip whenever state changes via saveState/render flow
            const origPushTx = window.pushTx || pushTx;
            window.pushTx = function(type, amount, memo){ origPushTx(type, amount, memo); updateTipText(); };
            const origSave = window.saveState || saveState;
            window.saveState = function(){ origSave(); updateTipText(); };

            // Also update whenever render is called (covers other UI flows)
            const origRender = window.render || render;
            window.render = function(){ origRender(); updateTipText(); };

        }catch(e){ console.warn('wallet tooltip setup failed', e); }
    })();

    connectBtn && connectBtn.addEventListener('click', function(){
        state.connected = !state.connected;
        saveState();
        render();
    });

    addBtn && addBtn.addEventListener('click', function(){
        const v = Number(amountInput.value || 0);
        if(!state.connected){ alert('Please connect wallet first.'); return; }
        if(!(v > 0)){ alert('Enter a positive amount.'); return; }
        state.balance = Number((state.balance + v).toFixed(8));
        pushTx('in', v, 'Deposit');
    });

    withdrawBtn && withdrawBtn.addEventListener('click', function(){
        const v = Number(amountInput.value || 0);
        if(!state.connected){ alert('Please connect wallet first.'); return; }
        if(!(v > 0)){ alert('Enter a positive amount.'); return; }
        if(v > state.balance){ alert('Insufficient balance.'); return; }
        state.balance = Number((state.balance - v).toFixed(8));
        pushTx('out', v, 'Withdraw');
    });

    if(clearTx){
        clearTx.addEventListener('click', function(){
            if(!confirm('Clear transaction history?')) return;
            state.tx = [];
            saveState();
            render();
        });
    }
});