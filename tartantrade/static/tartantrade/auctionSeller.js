// Auction Seller Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Countdown timer to display remaining auction time
    function updateCountdown() {
        const auctionTimeEl = document.querySelector('.auction-time');
        if (!auctionTimeEl) return;

        const endTimeStr = auctionTimeEl.dataset.endTime;
        const endTime = new Date(endTimeStr).getTime();
        const now = new Date().getTime();
        const timeLeft = endTime - now;

        const countdownEl = document.getElementById('countdown');
        if (!countdownEl) return;

        // Display "Auction ended" when time is up
        if (timeLeft <= 0) {
            countdownEl.textContent = "Auction ended";
            return;
        }

        // Calculate and format remaining time
        const days = Math.floor(timeLeft / (1000 * 60 * 60 * 24));
        const hours = Math.floor((timeLeft % (1000 * 60 * 60 * 24)) / (1000 * 60 * 60));
        const minutes = Math.floor((timeLeft % (1000 * 60 * 60)) / (1000 * 60));
        const seconds = Math.floor((timeLeft % (1000 * 60)) / 1000);

        countdownEl.textContent = `${days}d ${hours}h ${minutes}m ${seconds}s`;
    }

    // Initialize countdown timer with 1-second interval
    if (document.querySelector('.auction-time')) {
        updateCountdown();
        setInterval(updateCountdown, 1000);
    }

    // Setup product image gallery and navigation
    const setupGallery = function () {
        const thumbnails = document.querySelectorAll('.thumbnail');
        const mainImage = document.querySelector('.main-image');

        if (thumbnails.length > 0 && mainImage) {
            // Handle thumbnail click to update main image
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

    // Seller-specific modal handling for editing auction
    const setupModals = function () {
        const editAuctionModal = document.getElementById('editAuctionModal');
        if (!editAuctionModal) return;

        // Open edit auction modal when edit button is clicked
        const editAuctionBtn = document.querySelector('.btn-primary');
        if (editAuctionBtn) {
            editAuctionBtn.addEventListener('click', function (e) {
                if (this.tagName.toLowerCase() === 'a' && this.href.includes('edit_auction')) {
                    e.preventDefault();
                    editAuctionModal.style.display = 'block';
                }
            });
        }

        // Close modal when close button is clicked
        const closeModalBtns = document.querySelectorAll('.close-modal');
        closeModalBtns.forEach(button => {
            button.addEventListener('click', function () {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        });

        // Close modal when clicking outside the modal content
        window.addEventListener('click', function (event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        });
    };

    setupModals();

    // Form validation for auction edit form
    const setupForms = function () {
        const editAuctionForm = document.getElementById('edit-auction-form');
        if (!editAuctionForm) return;

        editAuctionForm.addEventListener('submit', function (e) {
            const endTimeInput = document.getElementById('end-time');
            const buyNowPriceInput = document.getElementById('buy-now-price');

            if (endTimeInput && buyNowPriceInput) {
                const endTime = new Date(endTimeInput.value);
                const now = new Date();

                // Validate that auction end time is in the future
                if (endTime <= now) {
                    e.preventDefault();
                    alert('Auction end time must be in the future.');
                    return;
                }

                // Additional validations can be added here
            }
        });
    };

    setupForms();

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