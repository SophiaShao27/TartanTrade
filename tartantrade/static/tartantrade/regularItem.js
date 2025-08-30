// Regular Item Page JavaScript

document.addEventListener('DOMContentLoaded', function () {
    // Setup image gallery with thumbnails and navigation
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

    // Initialize and manage modal popup windows
    const setupModals = function () {
        const buyNowModal = document.getElementById('buyNowModal');
        const watchlistModal = document.getElementById('addToWatchlistModal');
        const messageModal = document.getElementById('messageSellerModal');

        // Configure button triggers for each modal
        const buyNowButton = document.querySelector('.buy-now-button');
        if (buyNowButton && buyNowModal) {
            buyNowButton.addEventListener('click', function () {
                buyNowModal.style.display = 'block';
            });
        }

        const watchlistButton = document.querySelector('.watchlist-button');
        if (watchlistButton && watchlistModal) {
            watchlistButton.addEventListener('click', function () {
                watchlistModal.style.display = 'block';
            });
        }

        const messageButton = document.querySelector('.btn-message');
        if (messageButton && messageModal) {
            messageButton.addEventListener('click', function () {
                messageModal.style.display = 'block';
            });
        }

        // Handle modal close button clicks
        document.querySelectorAll('.close-modal').forEach(button => {
            button.addEventListener('click', function () {
                const modal = this.closest('.modal');
                if (modal) {
                    modal.style.display = 'none';
                }
            });
        });

        // Close modal when clicking outside content area
        window.addEventListener('click', function (event) {
            if (event.target.classList.contains('modal')) {
                event.target.style.display = 'none';
            }
        });
    };

    setupModals();

    // Handle watchlist functionality with state tracking
    const setupWatchlist = function () {
        const watchlistButton = document.querySelector('.watchlist-button');
        if (!watchlistButton) return;

        // Get current watchlist status from HTML data attribute
        const watchlistStatusElement = document.getElementById('watchlist-status');
        let isInWatchlist = false;

        if (watchlistStatusElement) {
            isInWatchlist = watchlistStatusElement.dataset.isInWatchlist === 'true';
        }

        // Update button appearance based on watchlist status
        function updateWatchlistButton() {
            if (isInWatchlist) {
                watchlistButton.innerHTML = '<i class="fas fa-heart"></i> Added to Watchlist';
                watchlistButton.classList.add('watched');
            } else {
                watchlistButton.innerHTML = '<i class="far fa-heart"></i> Add to Wishlist';
                watchlistButton.classList.remove('watched');
            }
        }

        updateWatchlistButton();

        // Handle AJAX form submission for watchlist updates
        const watchlistForm = document.querySelector('#watchlist-form');
        if (watchlistForm) {
            watchlistForm.addEventListener('submit', function (e) {
                e.preventDefault();
                const form = this;

                // Helper function to get CSRF token from cookies
                function getCookie(name) {
                    let cookieValue = null;
                    if (document.cookie && document.cookie !== '') {
                        const cookies = document.cookie.split(';');
                        for (let i = 0; i < cookies.length; i++) {
                            const cookie = cookies[i].trim();
                            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                                break;
                            }
                        }
                    }
                    return cookieValue;
                }

                const csrftoken = getCookie('csrftoken');

                // Send AJAX request to add item to watchlist
                fetch(form.action, {
                    method: 'POST',
                    body: new FormData(form),
                    headers: {
                        'X-Requested-With': 'XMLHttpRequest',
                        'X-CSRFToken': csrftoken
                    }
                })
                    .then(response => {
                        if (!response.ok) {
                            throw new Error('Network response was not ok');
                        }
                        return response.json();
                    })
                    .then(data => {
                        const watchlistModal = document.getElementById('addToWatchlistModal');
                        if (watchlistModal) {
                            watchlistModal.style.display = 'none';
                        }

                        isInWatchlist = true;
                        updateWatchlistButton();

                        // Show success notification
                        showSuccessMessage('Item added to your watchlist!');
                    })
                    .catch(error => {
                        console.error('Error:', error);
                        showSuccessMessage('An error occurred. Please try again.', 'error');
                    });
            });
        }
    };

    setupWatchlist();

    // Create and display notification messages
    function showSuccessMessage(message, type = 'success') {
        // Create notification element with styling
        const successMsg = document.createElement('div');
        successMsg.className = `alert alert-${type}`;
        successMsg.style.position = 'fixed';
        successMsg.style.top = '20px';
        successMsg.style.left = '50%';
        successMsg.style.transform = 'translateX(-50%)';
        successMsg.style.padding = '15px 25px';
        successMsg.style.borderRadius = '5px';
        successMsg.style.zIndex = '2000';

        // Style based on message type (success/error)
        if (type === 'success') {
            successMsg.style.backgroundColor = '#4CAF50';
            successMsg.style.color = 'white';
            successMsg.innerHTML = `<i class="fas fa-check-circle"></i> ${message}`;
        } else {
            successMsg.style.backgroundColor = '#f44336';
            successMsg.style.color = 'white';
            successMsg.innerHTML = `<i class="fas fa-exclamation-circle"></i> ${message}`;
        }

        document.body.appendChild(successMsg);

        // Auto-remove message after delay with fade effect
        setTimeout(() => {
            successMsg.style.opacity = '0';
            successMsg.style.transition = 'opacity 0.5s';
            setTimeout(() => {
                document.body.removeChild(successMsg);
            }, 500);
        }, 3000);
    }
});