// Mobile app JavaScript functionality
class MobilePOSApp {
    constructor() {
        this.cart = JSON.parse(localStorage.getItem('mobile_cart') || '[]');
        this.init();
    }

    init() {
        // Initialize app after DOM load
        if (document.readyState === 'loading') {
            document.addEventListener('DOMContentLoaded', () => this.initializeApp());
        } else {
            this.initializeApp();
        }
    }

    initializeApp() {
        this.updateCartCount();
        this.initializeEventListeners();
        this.loadDashboardData();
    }

    initializeEventListeners() {
        // Product search
        const searchInput = document.getElementById('productSearch');
        if (searchInput) {
            searchInput.addEventListener('input', (e) => this.filterProducts(e.target.value));
        }

        // Cart management
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('add-to-cart-btn')) {
                const productId = e.target.dataset.productId;
                const productName = e.target.dataset.productName;
                const productPrice = parseFloat(e.target.dataset.productPrice);
                this.addToCart(productId, productName, productPrice);
            }

            if (e.target.classList.contains('remove-from-cart')) {
                const index = parseInt(e.target.dataset.index);
                this.removeFromCart(index);
            }
        });

        // Sales form
        const salesForm = document.getElementById('salesForm');
        if (salesForm) {
            salesForm.addEventListener('submit', (e) => this.processSale(e));
        }

        // Quantity controls
        document.addEventListener('click', (e) => {
            if (e.target.classList.contains('qty-btn')) {
                const input = e.target.parentElement.querySelector('.qty-input');
                const change = e.target.classList.contains('qty-plus') ? 1 : -1;
                this.updateQuantity(input, change);
            }
        });
    }

    addToCart(productId, productName, productPrice) {
        const existingItem = this.cart.find(item => item.id === productId);
        
        if (existingItem) {
            existingItem.quantity += 1;
        } else {
            this.cart.push({
                id: productId,
                name: productName,
                price: productPrice,
                quantity: 1
            });
        }

        this.saveCart();
        this.updateCartCount();
        this.showToast(`${productName} agregado al carrito`, 'success');
        this.updateCartDisplay();
    }

    removeFromCart(index) {
        const item = this.cart[index];
        this.cart.splice(index, 1);
        this.saveCart();
        this.updateCartCount();
        this.showToast(`${item.name} eliminado del carrito`, 'info');
        this.updateCartDisplay();
    }

    updateQuantity(input, change) {
        const currentValue = parseInt(input.value) || 1;
        const newValue = Math.max(1, currentValue + change);
        input.value = newValue;

        // Update cart if this is in cart
        const index = parseInt(input.dataset.index);
        if (!isNaN(index) && this.cart[index]) {
            this.cart[index].quantity = newValue;
            this.saveCart();
            this.updateCartDisplay();
        }
    }

    saveCart() {
        localStorage.setItem('mobile_cart', JSON.stringify(this.cart));
    }

    updateCartCount() {
        const cartCount = this.cart.reduce((sum, item) => sum + item.quantity, 0);
        const cartBadges = document.querySelectorAll('.cart-count');
        cartBadges.forEach(badge => {
            badge.textContent = cartCount;
            badge.style.display = cartCount > 0 ? 'inline' : 'none';
        });
    }

    updateCartDisplay() {
        const cartItems = document.getElementById('cartItems');
        const cartTotal = document.getElementById('cartTotal');
        
        if (!cartItems) return;

        if (this.cart.length === 0) {
            cartItems.innerHTML = `
                <div class="empty-cart text-center py-4">
                    <i class="fas fa-shopping-cart fa-3x text-muted mb-3"></i>
                    <p class="text-muted">Tu carrito está vacío</p>
                </div>
            `;
            if (cartTotal) cartTotal.textContent = '₡0.00';
            return;
        }

        let total = 0;
        cartItems.innerHTML = this.cart.map((item, index) => {
            const subtotal = item.price * item.quantity;
            total += subtotal;
            return `
                <div class="cart-item mb-3">
                    <div class="d-flex justify-content-between align-items-center">
                        <div class="flex-grow-1">
                            <h6 class="mb-1">${item.name}</h6>
                            <small class="text-muted">₡${item.price.toFixed(2)} c/u</small>
                        </div>
                        <div class="quantity-controls">
                            <button type="button" class="btn btn-sm btn-outline-secondary qty-btn qty-minus">-</button>
                            <input type="number" class="form-control qty-input" value="${item.quantity}" min="1" data-index="${index}">
                            <button type="button" class="btn btn-sm btn-outline-secondary qty-btn qty-plus">+</button>
                        </div>
                        <div class="ms-3">
                            <strong>₡${subtotal.toFixed(2)}</strong>
                            <button type="button" class="btn btn-sm btn-outline-danger remove-from-cart ms-2" data-index="${index}">
                                <i class="fas fa-trash-alt"></i>
                            </button>
                        </div>
                    </div>
                </div>
            `;
        }).join('');

        if (cartTotal) {
            cartTotal.textContent = `₡${total.toFixed(2)}`;
        }
    }

    async processSale(e) {
        e.preventDefault();
        
        if (this.cart.length === 0) {
            this.showToast('El carrito está vacío', 'warning');
            return;
        }

        const formData = new FormData(e.target);
        const saleData = {
            items: this.cart,
            payment_method: formData.get('payment_method'),
            customer_name: formData.get('customer_name') || 'Cliente General',
            notes: formData.get('notes') || ''
        };

        try {
            const response = await fetch('/api/sales', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify(saleData)
            });

            const result = await response.json();

            if (response.ok) {
                this.cart = [];
                this.saveCart();
                this.updateCartCount();
                this.updateCartDisplay();
                
                this.showToast('Venta procesada exitosamente', 'success');
                
                // Show success modal
                const successModal = new bootstrap.Modal(document.getElementById('saleSuccessModal'));
                document.getElementById('saleReceiptNumber').textContent = result.sale_id;
                document.getElementById('saleReceiptTotal').textContent = `₡${result.total.toFixed(2)}`;
                successModal.show();

                // Reset form
                e.target.reset();
            } else {
                this.showToast(result.error || 'Error al procesar la venta', 'error');
            }
        } catch (error) {
            console.error('Error processing sale:', error);
            this.showToast('Error de conexión', 'error');
        }
    }

    async filterProducts(searchTerm) {
        const productGrid = document.getElementById('productGrid');
        if (!productGrid) return;

        try {
            const response = await fetch(`/api/products?search=${encodeURIComponent(searchTerm)}`);
            const products = await response.json();

            if (products.length === 0) {
                productGrid.innerHTML = `
                    <div class="col-12 text-center py-4">
                        <i class="fas fa-search fa-3x text-muted mb-3"></i>
                        <p class="text-muted">No se encontraron productos</p>
                    </div>
                `;
                return;
            }

            productGrid.innerHTML = products.map(product => `
                <div class="col-6 col-md-4 col-lg-3 mb-3">
                    <div class="product-card h-100">
                        <div class="product-image">
                            <i class="fas fa-box product-icon"></i>
                        </div>
                        <div class="product-info">
                            <h6 class="product-name">${product.nombre}</h6>
                            <p class="product-price">₡${product.precio_venta}</p>
                            <p class="product-stock ${product.stock_actual <= 5 ? 'low-stock' : ''}">
                                Stock: ${product.stock_actual}
                            </p>
                            <button class="btn btn-primary btn-sm add-to-cart-btn w-100" 
                                    data-product-id="${product.id}"
                                    data-product-name="${product.nombre}"
                                    data-product-price="${product.precio_venta}"
                                    ${product.stock_actual <= 0 ? 'disabled' : ''}>
                                ${product.stock_actual <= 0 ? 'Sin Stock' : 'Agregar'}
                            </button>
                        </div>
                    </div>
                </div>
            `).join('');
        } catch (error) {
            console.error('Error filtering products:', error);
            this.showToast('Error al cargar productos', 'error');
        }
    }

    async loadDashboardData() {
        const todaySales = document.getElementById('todaySales');
        const todayOrders = document.getElementById('todayOrders');
        const lowStock = document.getElementById('lowStock');

        if (!todaySales) return; // Not on dashboard page

        try {
            const response = await fetch('/api/dashboard');
            const data = await response.json();

            if (todaySales) todaySales.textContent = `₡${data.today_sales.toFixed(2)}`;
            if (todayOrders) todayOrders.textContent = data.today_orders;
            if (lowStock) lowStock.textContent = data.low_stock_count;

            // Load featured products
            this.loadFeaturedProducts(data.featured_products);
        } catch (error) {
            console.error('Error loading dashboard data:', error);
        }
    }

    loadFeaturedProducts(products) {
        const featuredProducts = document.getElementById('featuredProducts');
        if (!featuredProducts || !products) return;

        featuredProducts.innerHTML = products.map(product => `
            <div class="col-6 mb-3">
                <div class="featured-product-card">
                    <h6 class="mb-1">${product.nombre}</h6>
                    <p class="text-primary mb-2">₡${product.precio_venta}</p>
                    <button class="btn btn-sm btn-primary add-to-cart-btn" 
                            data-product-id="${product.id}"
                            data-product-name="${product.nombre}"
                            data-product-price="${product.precio_venta}">
                        Agregar
                    </button>
                </div>
            </div>
        `).join('');
    }

    showToast(message, type = 'info') {
        // Create toast element
        const toastId = 'toast-' + Date.now();
        const toast = document.createElement('div');
        toast.id = toastId;
        toast.className = `toast align-items-center text-white bg-${type === 'error' ? 'danger' : type === 'success' ? 'success' : type === 'warning' ? 'warning' : 'info'} border-0`;
        toast.setAttribute('role', 'alert');
        toast.innerHTML = `
            <div class="d-flex">
                <div class="toast-body">
                    ${message}
                </div>
                <button type="button" class="btn-close btn-close-white me-2 m-auto" data-bs-dismiss="toast"></button>
            </div>
        `;

        // Add to toast container
        let toastContainer = document.getElementById('toastContainer');
        if (!toastContainer) {
            toastContainer = document.createElement('div');
            toastContainer.id = 'toastContainer';
            toastContainer.className = 'toast-container position-fixed top-0 end-0 p-3';
            toastContainer.style.zIndex = '9999';
            document.body.appendChild(toastContainer);
        }

        toastContainer.appendChild(toast);

        // Show toast
        const bsToast = new bootstrap.Toast(toast, {
            autohide: true,
            delay: 3000
        });
        bsToast.show();

        // Remove from DOM after hiding
        toast.addEventListener('hidden.bs.toast', () => {
            toast.remove();
        });
    }

    // Print receipt functionality
    printReceipt(saleId) {
        window.open(`/api/receipt/${saleId}`, '_blank');
    }

    // PWA installation
    initializePWA() {
        let deferredPrompt;

        window.addEventListener('beforeinstallprompt', (e) => {
            e.preventDefault();
            deferredPrompt = e;
            
            // Show install button
            const installBtn = document.getElementById('installBtn');
            if (installBtn) {
                installBtn.style.display = 'block';
                installBtn.addEventListener('click', () => {
                    deferredPrompt.prompt();
                    deferredPrompt.userChoice.then((choiceResult) => {
                        if (choiceResult.outcome === 'accepted') {
                            console.log('PWA installed');
                        }
                        deferredPrompt = null;
                        installBtn.style.display = 'none';
                    });
                });
            }
        });
    }
}

// Initialize app
const mobilePOS = new MobilePOSApp();

// Service Worker registration for PWA
if ('serviceWorker' in navigator) {
    window.addEventListener('load', () => {
        navigator.serviceWorker.register('/static/js/sw.js')
            .then((registration) => {
                console.log('SW registered: ', registration);
            })
            .catch((registrationError) => {
                console.log('SW registration failed: ', registrationError);
            });
    });
}
