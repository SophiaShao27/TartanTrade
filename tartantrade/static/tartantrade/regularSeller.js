// Regular Item Seller Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Setup product image gallery with navigation
    const setupGallery = function () {
        const thumbnails = document.querySelectorAll('.thumbnail');
        const mainImage = document.querySelector('.main-image');

        if (thumbnails.length > 0 && mainImage) {
            // Handle thumbnail clicks to update main image
            thumbnails.forEach(thumb => {
                thumb.addEventListener('click', function () {
                    thumbnails.forEach(t => t.classList.remove('active'));
                    this.classList.add('active');
                    mainImage.src = this.querySelector('img').src;
                });
            });

            // Setup previous/next navigation buttons
            const prevBtn = document.querySelector('.gallery-btn:first-child');
            const nextBtn = document.querySelector('.gallery-btn:last-child');

            if (prevBtn) {
                prevBtn.addEventListener('click', function () {
                    const activeThumb = document.querySelector('.thumbnail.active');
                    if (activeThumb) {
                        const prevThumb = activeThumb.previousElementSibling || thumbnails[thumbnails.length - 1];
                        prevThumb.click();
                    }
                });
            }

            if (nextBtn) {
                nextBtn.addEventListener('click', function () {
                    const activeThumb = document.querySelector('.thumbnail.active');
                    if (activeThumb) {
                        const nextThumb = activeThumb.nextElementSibling || thumbnails[0];
                        nextThumb.click();
                    }
                });
            }
        }
    };

    setupGallery();

    // Handle "Convert to Auction" modal for seller
    const setupModals = function () {
        const convertModal = document.getElementById('convertToAuctionModal');
        if (!convertModal) return;

        // Configure button to open convert modal
        const convertBtn = document.querySelector('.convert-auction-btn');
        if (convertBtn) {
            convertBtn.addEventListener('click', function () {
                convertModal.style.display = 'block';
            });
        }

        // Setup close button functionality
        const closeModalBtns = document.querySelectorAll('.close-modal');
        closeModalBtns.forEach(button => {
            button.addEventListener('click', function () {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        });

        // Close modal when clicking outside content
        window.addEventListener('click', function (event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        });
    };

    setupModals();

    // Setup auction form validation and defaults
    const setupForms = function () {
        const auctionForm = document.getElementById('auction-form');
        if (!auctionForm) return;

        // Set default auction end time to 7 days from now
        const endTimeInput = document.getElementById('end_time');
        if (endTimeInput) {
            const now = new Date();
            now.setDate(now.getDate() + 7);
            const formattedDate = now.toISOString().slice(0, 16);
            endTimeInput.value = formattedDate;
        }

        // Validate auction settings before submission
        auctionForm.addEventListener('submit', function (e) {
            const startPriceInput = document.getElementById('start_price');
            const endTimeInput = document.getElementById('end_time');
            const buyNowPriceInput = document.getElementById('buy_now_price');

            if (startPriceInput && endTimeInput && buyNowPriceInput) {
                const startPrice = parseFloat(startPriceInput.value);
                const buyNowPrice = parseFloat(buyNowPriceInput.value);
                const endTime = new Date(endTimeInput.value);
                const now = new Date();

                // Ensure auction end time is in the future
                if (endTime <= now) {
                    e.preventDefault();
                    showMessage('Auction end time must be in the future.', 'error');
                    return;
                }

                // Ensure buy-now price is higher than starting price
                if (buyNowPrice <= startPrice) {
                    e.preventDefault();
                    showMessage('Buy Now price must be higher than Starting price.', 'error');
                    return;
                }
            }
        });
    };

    setupForms();

    // Add confirmation dialog for item deletion
    const setupDeleteConfirmation = function () {
        const deleteBtn = document.querySelector('a[href*="delete_item"]');
        if (deleteBtn) {
            deleteBtn.addEventListener('click', function (e) {
                const confirmed = confirm('Are you sure you want to delete this item? This action cannot be undone.');
                if (!confirmed) {
                    e.preventDefault();
                }
            });
        }
    };

    setupDeleteConfirmation();

    // Create and display notification messages
    function showMessage(message, type = 'success') {
        // Create notification element with styling
        const msgElement = document.createElement('div');
        msgElement.className = `alert alert-${type}`;
        msgElement.style.position = 'fixed';
        msgElement.style.top = '20px';
        msgElement.style.left = '50%';
        msgElement.style.transform = 'translateX(-50%)';
        msgElement.style.padding = '15px 25px';
        msgElement.style.borderRadius = '5px';
        msgElement.style.zIndex = '2000';

        // Style based on message type (success/error)
        if (type === 'success') {
            msgElement.style.backgroundColor = '#4CAF50';
            msgElement.style.color = 'white';
            msgElement.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        } else {
            msgElement.style.backgroundColor = '#f44336';
            msgElement.style.color = 'white';
            msgElement.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        }

        document.body.appendChild(msgElement);

        // Auto-remove message after delay with fade effect
        setTimeout(() => {
            msgElement.style.opacity = '0';
            msgElement.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                document.body.removeChild(msgElement);
            }, 500);
        }, 3000);
    }
});