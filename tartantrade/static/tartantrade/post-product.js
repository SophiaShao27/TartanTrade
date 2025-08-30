document.addEventListener('DOMContentLoaded', function () {
    // Image preview functionality for product photo upload
    const imageInput = document.getElementById('id_picture');
    const imagePreview = document.getElementById('image-preview');
    const previewImg = document.getElementById('preview-img');

    imageInput.addEventListener('change', function () {
        if (this.files && this.files[0]) {
            const reader = new FileReader();

            // Display image preview when file is selected
            reader.onload = function (e) {
                previewImg.src = e.target.result;
                imagePreview.classList.add('has-image');
            }

            reader.readAsDataURL(this.files[0]);
        } else {
            // Reset preview if no file is selected
            previewImg.src = '#';
            imagePreview.classList.remove('has-image');
        }
    });

    // Auction toggle functionality - shows/hides auction options
    const auctionToggle = document.getElementById('auction-toggle');
    const auctionOptions = document.getElementById('auction-options');
    const startPriceInput = document.getElementById('id_start_price');
    const endTimeInput = document.getElementById('id_end_time');
    const priceInput = document.getElementById('id_price');

    // Restore auction options visibility if toggle was previously checked
    if (auctionToggle.checked) {
        auctionOptions.classList.add('visible');
        startPriceInput.required = true;
        endTimeInput.required = true;
    }

    auctionToggle.addEventListener('change', function () {
        if (this.checked) {
            // Show auction options and make fields required
            auctionOptions.classList.add('visible');
            startPriceInput.required = true;
            endTimeInput.required = true;

            // Set default start price as half of buy now price
            if (!startPriceInput.value) {
                const buyNowPrice = priceInput.value || 0;
                startPriceInput.value = (buyNowPrice / 2).toFixed(2);
            }

            // Set default end time as 7 days from now
            if (!endTimeInput.value) {
                const now = new Date();
                now.setDate(now.getDate() + 7);
                const formattedDate = now.toISOString().slice(0, 16);
                endTimeInput.value = formattedDate;
            }
        } else {
            // Hide auction options and make fields optional
            auctionOptions.classList.remove('visible');
            startPriceInput.required = false;
            endTimeInput.required = false;
        }
    });

    // Form validation before submission
    const form = document.getElementById('product-form');

    form.addEventListener('submit', function (e) {
        let isValid = true;

        // Basic validation for required fields
        const title = document.getElementById('id_title').value;
        const price = document.getElementById('id_price').value;
        const description = document.getElementById('id_description').value;

        if (!title || !price || !description) {
            isValid = false;
            alert('Please fill in all required fields');
        }

        // Additional validation for auction-specific fields
        if (auctionToggle.checked) {
            const startPrice = startPriceInput.value;
            const endTime = endTimeInput.value;
            const buyNowPrice = priceInput.value;

            if (!startPrice || !endTime) {
                isValid = false;
                alert('Please fill in all auction fields');
            }

            // Ensure starting price is less than buy now price
            if (parseFloat(startPrice) >= parseFloat(buyNowPrice)) {
                alert('Starting price must be less than buy now price');
                isValid = false;
            }

            // Ensure auction end time is in the future
            const now = new Date();
            const endTimeDate = new Date(endTime);

            if (endTimeDate <= now) {
                alert('Auction end time must be in the future');
                isValid = false;
            }
        }

        // Prevent form submission if validation fails
        if (!isValid) {
            e.preventDefault();
        }
    });
});