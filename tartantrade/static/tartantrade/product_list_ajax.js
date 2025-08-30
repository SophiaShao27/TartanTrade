// product-list.js - 用于Ajax实现实时产品列表更新的JavaScript代码

document.addEventListener('DOMContentLoaded', function() {
    // 获取DOM元素
    const filterForm = document.getElementById('filter-form');
    const searchForm = document.querySelector('.top-search-form');
    const productsContainer = document.getElementById('products-container');
    const totalProductsCount = document.getElementById('total-products-count');
    const paginationContainer = document.getElementById('pagination-container');
    const sortDropdownItems = document.querySelectorAll('.sort-dropdown-item');
    const messageContainer = document.getElementById('message-container');
    const loadingSpinner = document.getElementById('loading-spinner');
    const noProductsMessage = document.getElementById('no-products-message');
    const clearFiltersBtn = document.getElementById('clear-filters-btn');
    const categoryRadios = document.querySelectorAll('.category-radio');
      
  
    // 存储当前的筛选状态
    let currentFilters = {
      category: getUrlParameter('category') || 'All',
      min_price: getUrlParameter('min_price') || '',
      max_price: getUrlParameter('max_price') || '',
      conditions: getUrlParameter('condition') ?
                   Array.isArray(getUrlParameter('condition')) ?
                   getUrlParameter('condition') :
                   [getUrlParameter('condition')] :
                   [],
      search_query: getUrlParameter('nav_top_search') || '',
      sort_by: getUrlParameter('sort') || 'default',
      page: getUrlParameter('page') || 1
    };
  
    // 监听筛选表单提交
    if (filterForm) {
      filterForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(filterForm);
  
        // 更新当前筛选状态
        currentFilters.min_price = formData.get('min_price') || '';
        currentFilters.max_price = formData.get('max_price') || '';
        currentFilters.conditions = formData.getAll('condition');
        currentFilters.page = 1; // 重置页码
  
        // 执行筛选
        fetchProducts();
      });
    }
  
    // 监听搜索表单提交
    if (searchForm) {
      searchForm.addEventListener('submit', function(e) {
        e.preventDefault();
        const formData = new FormData(searchForm);
  
        // 更新搜索查询
        currentFilters.search_query = formData.get('nav_top_search') || '';
        currentFilters.page = 1; // 重置页码
  
        // 执行筛选
        fetchProducts();
      });
    }
  
    // 监听类别单选按钮变更
    if (categoryRadios) {
      categoryRadios.forEach(radio => {
        radio.addEventListener('change', function() {
          // 更新类别并清除搜索查询
          currentFilters.category = this.value;
          currentFilters.search_query = '';
          currentFilters.page = 1; // 重置页码
  
          // 清除搜索框的值
          const searchInput = document.querySelector('input[name="nav_top_search"]');
          if (searchInput) {
            searchInput.value = '';
          }
  
          // 执行筛选
          fetchProducts();
        });
      });
    }
  
    // 监听排序选项点击
    if (sortDropdownItems) {
      sortDropdownItems.forEach(item => {
        item.addEventListener('click', function(e) {
          e.preventDefault();
  
          // 更新排序方式
          currentFilters.sort_by = this.getAttribute('data-sort');
  
          // 更新排序按钮文本
          const sortDropdownButton = document.getElementById('sortDropdown');
          if (sortDropdownButton) {
            let sortText = 'Default';
            if (currentFilters.sort_by === 'newest') {
              sortText = 'Newest First';
            } else if (currentFilters.sort_by === 'price_low') {
              sortText = 'Price: Low to High';
            } else if (currentFilters.sort_by === 'price_high') {
              sortText = 'Price: High to Low';
            }
            sortDropdownButton.textContent = 'Sort By: ' + sortText;
          }
  
          // 执行筛选
          fetchProducts();
        });
      });
    }
  
    // 清除所有筛选条件
    if (clearFiltersBtn) {
      clearFiltersBtn.addEventListener('click', function() {
        // 重置所有筛选条件
        currentFilters = {
          category: 'All',
          min_price: '',
          max_price: '',
          conditions: [],
          search_query: '',
          sort_by: 'default',
          page: 1
        };
  
        // 重置表单UI
        resetFilterFormUI();
  
        // 执行筛选
        fetchProducts();
      });
    }
  
    // 处理分页点击
    function setupPaginationListeners() {
      const paginationLinks = document.querySelectorAll('.page-link');
      if (paginationLinks) {
        paginationLinks.forEach(link => {
          link.addEventListener('click', function(e) {
            e.preventDefault();
  
            // 获取页码
            const page = this.getAttribute('data-page');
            if (page) {
              currentFilters.page = page;
  
              // 执行筛选并滚动到顶部
              fetchProducts();
              window.scrollTo(0, 0);
            }
          });
        });
      }
    }
  
    // 重置筛选表单UI
    function resetFilterFormUI() {
      // 重置类别单选按钮
      const allCategoryRadio = document.getElementById('allCheck');
      if (allCategoryRadio) {
        allCategoryRadio.checked = true;
      }
  
      // 重置价格输入框
      const minPriceInput = document.querySelector('input[name="min_price"]');
      const maxPriceInput = document.querySelector('input[name="max_price"]');
      if (minPriceInput) minPriceInput.value = '';
      if (maxPriceInput) maxPriceInput.value = '';
  
      // 重置条件复选框
      const conditionCheckboxes = document.querySelectorAll('input[name="condition"]');
      if (conditionCheckboxes) {
        conditionCheckboxes.forEach(checkbox => {
          checkbox.checked = false;
        });
      }
  
      // 重置搜索框
      const searchInput = document.querySelector('input[name="nav_top_search"]');
      if (searchInput) {
        searchInput.value = '';
      }
  
      // 重置排序下拉菜单
      const sortDropdownButton = document.getElementById('sortDropdown');
      if (sortDropdownButton) {
        sortDropdownButton.textContent = 'Sort By: Default';
      }
    }
  
    // 通过Ajax获取产品数据
    function fetchProducts() {
      // 显示加载中状态
      if (loadingSpinner) loadingSpinner.classList.remove('d-none');
      if (productsContainer) productsContainer.classList.add('d-none');
      if (noProductsMessage) noProductsMessage.classList.add('d-none');
  
      // 构建查询参数
      const params = new URLSearchParams();
      if (currentFilters.category && currentFilters.category !== 'All') {
        params.append('category', currentFilters.category);
      }
      if (currentFilters.min_price) {
        params.append('min_price', currentFilters.min_price);
      }
      if (currentFilters.max_price) {
        params.append('max_price', currentFilters.max_price);
      }
      if (currentFilters.conditions && currentFilters.conditions.length) {
        currentFilters.conditions.forEach(condition => {
          params.append('condition', condition);
        });
      }
      if (currentFilters.search_query) {
        params.append('nav_top_search', currentFilters.search_query);
      }
      if (currentFilters.sort_by && currentFilters.sort_by !== 'default') {
        params.append('sort', currentFilters.sort_by);
      }
      if (currentFilters.page && currentFilters.page !== 1) {
        params.append('page', currentFilters.page);
      }
  
      // 更新URL，但不刷新页面
      const newUrl = window.location.pathname + (params.toString() ? '?' + params.toString() : '');
      window.history.pushState({ filters: currentFilters }, '', newUrl);
  
      // 发送Ajax请求
      fetch('/api/products?' + params.toString())
        .then(response => {
          if (!response.ok) {
            throw new Error('Network response was not ok');
          }
          return response.json();
        })
        .then(data => {
          // 更新产品列表
          updateProductsList(data);
  
          // 更新分页
          updatePagination(data);
  
          // 更新产品数量显示
          if (totalProductsCount) {
            totalProductsCount.textContent = data.total_products;
            // 单数或复数显示
            const itemsText = document.getElementById('items-text');
            if (itemsText) {
              itemsText.textContent = data.total_products === 1 ? 'item' : 'items';
            }
          }
  
          // 更新页面标题
          updatePageTitle();
  
          // 设置分页点击监听
          setupPaginationListeners();
  
          // 隐藏加载中状态
          if (loadingSpinner) loadingSpinner.classList.add('d-none');
  
          // 显示产品列表或无产品消息
          if (data.products && data.products.length) {
            if (productsContainer) productsContainer.classList.remove('d-none');
            if (noProductsMessage) noProductsMessage.classList.add('d-none');
          } else {
            if (productsContainer) productsContainer.classList.add('d-none');
            if (noProductsMessage) noProductsMessage.classList.remove('d-none');
          }
        })
        .catch(error => {
          console.error('Error fetching products:', error);
  
          // 显示错误消息
          showMessage('An error occurred while loading products. Please try again.', 'danger');
  
          // 隐藏加载中状态
          if (loadingSpinner) loadingSpinner.classList.add('d-none');
        });
    }
  
    // 更新产品列表
    function updateProductsList(data) {
      if (!productsContainer) return;
  
      // 清空现有产品
      productsContainer.innerHTML = '';
  
      if (!data.products || !data.products.length) return;
  
      // 创建产品卡片行
      let row = document.createElement('div');
      row.className = 'row';
  
      // 遍历产品数据
      data.products.forEach(product => {
        // 创建产品卡片列
        const col = document.createElement('div');
        col.className = 'col-md-4 mb-4';
  
        // 构建产品卡片HTML
        col.innerHTML = `
          <div class="card product-card h-100">
            <div class="product-img-container">
              ${product.picture ? 
                `<img src="${product.picture}" class="product-img" alt="${product.title}">` : 
                `<div class="bg-light text-center py-5 h-100">No Image</div>`}
            </div>
            <div class="card-body">
              <h5 class="card-title">${product.title}</h5>
              <p class="card-text text-muted small">${product.category}</p>
              <p class="card-text">${product.description.length > 100 ? 
                product.description.substring(0, 100) + '...' : product.description}</p>
              <div class="d-flex justify-content-between align-items-center mt-3">
                <span class="text-danger fw-bold fs-5">$${product.price.toFixed(2)}</span>
                <span class="badge bg-light text-dark border">${product.condition}</span>
              </div>
            </div>
            <div class="card-footer bg-white border-top-0">
              <div class="d-grid">
                ${data.is_authenticated ? 
                  `<button class="btn btn-danger w-100 add-to-cart-btn" data-product-id="${product.id}">
                     <i class="bi bi-cart-plus"></i> Add to Cart
                   </button>` : 
                  `<button class="btn btn-danger" onclick="showLoginAlert()">Add to Cart</button>`}
              </div>
            </div>
          </div>
        `;
  
        // 添加到行中
        row.appendChild(col);
      });
  
      // 添加到容器
      productsContainer.appendChild(row);
  
      // 设置"添加到购物车"按钮的点击事件
      setupAddToCartListeners();
    }
  
    // 更新分页控件
    function updatePagination(data) {
      if (!paginationContainer) return;
  
      // 清空现有分页
      paginationContainer.innerHTML = '';
  
      if (!data.total_pages || data.total_pages <= 1) return;
  
      // 创建分页HTML
      let paginationHtml = `
        <nav aria-label="Page navigation" class="mt-4">
          <ul class="pagination justify-content-center">
      `;
  
      // 首页和上一页按钮
      if (data.current_page > 1) {
        paginationHtml += `
          <li class="page-item">
            <a class="page-link" href="#" data-page="1" aria-label="First">
              <span aria-hidden="true">&laquo;&laquo;</span>
            </a>
          </li>
          <li class="page-item">
            <a class="page-link" href="#" data-page="${data.current_page - 1}" aria-label="Previous">
              <span aria-hidden="true">&laquo;</span>
            </a>
          </li>
        `;
      }
  
      // 页码按钮
      for (let i = 1; i <= data.total_pages; i++) {
        if (
          i <= 5 ||
          i >= data.total_pages - 4 ||
          (i >= data.current_page - 2 && i <= data.current_page + 2)
        ) {
          paginationHtml += `
            <li class="page-item ${data.current_page === i ? 'active' : ''}">
              <a class="page-link" href="#" data-page="${i}">${i}</a>
            </li>
          `;
        } else if (i === 6 || i === data.total_pages - 5) {
          paginationHtml += `
            <li class="page-item disabled">
              <span class="page-link">...</span>
            </li>
          `;
        }
      }
  
      // 下一页和末页按钮
      if (data.current_page < data.total_pages) {
        paginationHtml += `
          <li class="page-item">
            <a class="page-link" href="#" data-page="${data.current_page + 1}" aria-label="Next">
              <span aria-hidden="true">&raquo;</span>
            </a>
          </li>
          <li class="page-item">
            <a class="page-link" href="#" data-page="${data.total_pages}" aria-label="Last">
              <span aria-hidden="true">&raquo;&raquo;</span>
            </a>
          </li>
        `;
      }
  
      paginationHtml += `
          </ul>
        </nav>
      `;
  
      // 添加到容器
      paginationContainer.innerHTML = paginationHtml;
    }
  
    // 更新页面标题
    function updatePageTitle() {
      const titleElement = document.querySelector('.product-list-title');
      if (!titleElement) return;
  
      let titleText = '';
  
      if (currentFilters.search_query) {
        titleText = `Search results for "${currentFilters.search_query}"`;
        if (currentFilters.category && currentFilters.category !== 'All') {
          titleText += ` in ${currentFilters.category}`;
        }
      } else {
        titleText = currentFilters.category !== 'All' ?
                   `${currentFilters.category} Products` :
                   'All Products';
      }
  
      titleElement.textContent = titleText;
    }
  
    // 设置"添加到购物车"按钮的点击事件
    function setupAddToCartListeners() {
      const addToCartButtons = document.querySelectorAll('.add-to-cart-btn');
      if (addToCartButtons) {
        addToCartButtons.forEach(button => {
          button.addEventListener('click', function() {
            const productId = this.getAttribute('data-product-id');
            if (productId) {
              addToCart(productId);
            }
          });
        });
      }
    }
  
    // 添加商品到购物车
    function addToCart(productId) {
      // 获取CSRF令牌
      const csrfToken = document.querySelector('meta[name="csrf-token"]').getAttribute('content');
  
      // 发送Ajax请求
      fetch('/api/add-to-cart', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
          'X-CSRFToken': csrfToken
        },
        body: JSON.stringify({
          product_id: productId,
          quantity: 1
        })
      })
      .then(response => {
        if (!response.ok) {
          throw new Error('Network response was not ok');
        }
        return response.json();
      })
      .then(data => {
        if (data.success) {
          // 显示成功消息
          showMessage('Product added to cart successfully!', 'success');
  
          // 更新购物车数量
          updateCartCount();
        } else {
          // 显示错误消息
          showMessage(data.error || 'Failed to add product to cart.', 'danger');
        }
      })
      .catch(error => {
        console.error('Error adding product to cart:', error);
        showMessage('An error occurred. Please try again.', 'danger');
      });
    }
  
    // 更新购物车数量
    function updateCartCount() {
      fetch('/api/cart-count')
        .then(response => response.json())
        .then(data => {
          const cartCountElement = document.getElementById('cart-count');
          if (cartCountElement) {
            cartCountElement.textContent = data.count;
          }
        })
        .catch(error => {
          console.error('Error updating cart count:', error);
        });
    }
  
    // 显示消息
    function showMessage(message, type) {
      if (!messageContainer) return;
  
      // 创建消息元素
      const alertDiv = document.createElement('div');
      alertDiv.className = `alert alert-${type} alert-dismissible fade show`;
      alertDiv.innerHTML = `
        ${message}
        <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Close"></button>
      `;
  
      // 添加到容器
      messageContainer.appendChild(alertDiv);
  
      // 5秒后自动移除
      setTimeout(() => {
        alertDiv.remove();
      }, 5000);
    }
  
    // 获取URL参数
    function getUrlParameter(name) {
      const urlParams = new URLSearchParams(window.location.search);
      return urlParams.get(name);
    }
  
    // 初始化页面
    function initPage() {
      // 如果URL中有筛选参数，使用这些参数
      if (window.location.search) {
        // 设置UI以匹配URL参数
        setFilterUIFromURL();
  
        // 无需立即获取产品，因为页面加载时Django已经渲染了初始产品列表
  
        // 设置分页点击监听
        setupPaginationListeners();
  
        // 设置"添加到购物车"按钮的点击事件
        setupAddToCartListeners();
      }
  
      // 处理浏览器返回/前进按钮
      window.addEventListener('popstate', function(event) {
        if (event.state && event.state.filters) {
          currentFilters = event.state.filters;
          setFilterUIFromState();
          fetchProducts();
        } else {
          // 如果没有状态，重置为初始状态
          window.location.reload();
        }
      });
    }
  
    // 根据URL参数设置筛选UI
    function setFilterUIFromURL() {
      // 设置类别
      const category = getUrlParameter('category');
      if (category) {
        const categoryRadio = document.getElementById(`${category.toLowerCase()}Check`);
        if (categoryRadio) {
          categoryRadio.checked = true;
        }
      } else {
        const allCategoryRadio = document.getElementById('allCheck');
        if (allCategoryRadio) {
          allCategoryRadio.checked = true;
        }
      }
  
      // 设置价格范围
      const minPrice = getUrlParameter('min_price');
      const maxPrice = getUrlParameter('max_price');
      const minPriceInput = document.querySelector('input[name="min_price"]');
      const maxPriceInput = document.querySelector('input[name="max_price"]');
      if (minPriceInput && minPrice) minPriceInput.value = minPrice;
      if (maxPriceInput && maxPrice) maxPriceInput.value = maxPrice;
  
      // 设置条件复选框
      const conditions = getUrlParameter('condition');
      if (conditions) {
        const conditionValues = Array.isArray(conditions) ? conditions : [conditions];
        conditionValues.forEach(condition => {
          const conditionId = condition.replace(/\s+/g, '').toLowerCase() + 'Check';
          const checkbox = document.getElementById(conditionId);
          if (checkbox) {
            checkbox.checked = true;
          }
        });
      }
  
      // 设置搜索框
      const searchQuery = getUrlParameter('nav_top_search');
      const searchInput = document.querySelector('input[name="nav_top_search"]');
      if (searchInput && searchQuery) {
        searchInput.value = searchQuery;
      }
  
      // 设置排序下拉菜单
      const sortBy = getUrlParameter('sort');
      const sortDropdownButton = document.getElementById('sortDropdown');
      if (sortDropdownButton && sortBy) {
        let sortText = 'Default';
        if (sortBy === 'newest') {
          sortText = 'Newest First';
        } else if (sortBy === 'price_low') {
          sortText = 'Price: Low to High';
        } else if (sortBy === 'price_high') {
          sortText = 'Price: High to Low';
        }
        sortDropdownButton.textContent = 'Sort By: ' + sortText;
      }
    }
  
    // 根据当前状态设置筛选UI
    function setFilterUIFromState() {
      // 设置类别
      const categoryRadio = document.getElementById(`${currentFilters.category.toLowerCase()}Check`);
      if (categoryRadio) {
        categoryRadio.checked = true;
      }
  
      // 设置价格范围
      const minPriceInput = document.querySelector('input[name="min_price"]');
      const maxPriceInput = document.querySelector('input[name="max_price"]');
      if (minPriceInput) minPriceInput.value = currentFilters.min_price;
      if (maxPriceInput) maxPriceInput.value = currentFilters.max_price;
  
      // 设置条件复选框
      const conditionCheckboxes = document.querySelectorAll('input[name="condition"]');
      if (conditionCheckboxes) {
        conditionCheckboxes.forEach(checkbox => {
          checkbox.checked = currentFilters.conditions.includes(checkbox.value);
        });
      }
  
      // 设置搜索框
      const searchInput = document.querySelector('input[name="nav_top_search"]');
      if (searchInput) {
        searchInput.value = currentFilters.search_query;
      }
  
      // 设置排序下拉菜单
      const sortDropdownButton = document.getElementById('sortDropdown');
      if (sortDropdownButton) {
        let sortText = 'Default';
        if (currentFilters.sort_by === 'newest') {
          sortText = 'Newest First';
        } else if (currentFilters.sort_by === 'price_low') {
          sortText = 'Price: Low to High';
        } else if (currentFilters.sort_by === 'price_high') {
          sortText = 'Price: High to Low';
        }
        sortDropdownButton.textContent = 'Sort By: ' + sortText;
      }
    }
  
    // 登录提醒函数
    function showLoginAlert() {
      alert("Please login to access this feature!");
    }
  
    // 初始化页面
    initPage();
  
    // 如果需要实时更新，可以设置一个轮询函数
    // 例如每30秒检查一次是否有新产品
    if (document.body.classList.contains('enable-realtime-updates')) {
      setInterval(function() {
        // 获取最新的产品数量
        fetch('/api/products-count')
          .then(response => response.json())
          .then(data => {
            // 如果产品数量变了，刷新产品列表
            if (data.count !== parseInt(totalProductsCount.textContent)) {
              fetchProducts();
            }
          })
          .catch(error => {
            console.error('Error checking for new products:', error);
          });
      }, 30000); // 30秒
    }

    document.querySelectorAll('.add-to-cart-custom').forEach(function (btn) {
        btn.addEventListener('click', function () {
          const productId = this.dataset.productId;
          fetch('/cart/toggle/', {
            method: 'POST',
            headers: {
              'Content-Type': 'application/json',
              'X-CSRFToken': getCSRFToken(),
            },
            body: JSON.stringify({ product_id: productId })
          })
          .then(response => response.json())
          .then(data => {
            if (data.status === 'added') {
              alert("Added to your cart successfully!");
            } else if (data.status === 'removed') {
              alert("Removed from cart.");
            } else {
              alert("Something went wrong.");
            }
          })
          .catch(error => console.error("Error:", error));
        });
      });
      
  });