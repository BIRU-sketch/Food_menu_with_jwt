var orderCount = 0
var TotalPrice = 0
var orderItems = {}

function saveOrderData() {
    localStorage.setItem('orderCount', orderCount)
    localStorage.setItem('TotalPrice', TotalPrice)
    localStorage.setItem('orderItems', JSON.stringify(orderItems))
}

function loadOrderData() {
    var savedCount = localStorage.getItem('orderCount')
    var savedTotal = localStorage.getItem('TotalPrice')
    var savedItems = localStorage.getItem('orderItems')
    
    if (savedCount !== null) {
        orderCount = parseInt(savedCount)
    }
    if (savedTotal !== null) {
        TotalPrice = parseInt(savedTotal)
    }
    if (savedItems !== null) {
        orderItems = JSON.parse(savedItems)
    }
}

function updateSummary() {
    document.getElementById('order-count').innerText = 'Orders: ' + orderCount
    document.getElementById('order-total').innerText = 'Total: ' + TotalPrice + ' birr'

    var itemsEl = document.getElementById('order-items')
    itemsEl.innerHTML = ''

    var hasItems = false
    for (var itemName in orderItems) {
        var itemLine = document.createElement('p')
        itemLine.innerText = orderItems[itemName] + ' x ' + itemName
        itemsEl.appendChild(itemLine)
        hasItems = true
    }

    if (!hasItems) {
        itemsEl.innerText = 'No items yet'
    }
}

function handleOrderClick(event) {
    var target = event.target
    var card = target.parentNode
    var foodName = card.getElementsByClassName('food-card')[0].innerText
    var priceText = card.getElementsByClassName('price')[0].innerText
    var price = Number(priceText.replace(/[^0-9]/g, ''))

    orderCount = orderCount + 1
    TotalPrice = TotalPrice + price

    if (foodName in orderItems) {
        orderItems[foodName] = orderItems[foodName] + 1
    } else {
        orderItems[foodName] = 1
    }

    updateSummary()
    saveOrderData()
    alert('Order added succesfully.')
}

function showCurrentOrder(order) {
    var card = document.getElementsByClassName('orders-card')[0]
    card.innerHTML = ''

    var h3 = document.createElement('h3')
    h3.textContent = 'Your Order'
    card.appendChild(h3)

    for (var i = 0; i < order.items.length; i++) {
        var item = order.items[i]
        var p = document.createElement('p')
        p.textContent = item.quantity + ' x ' + item.name + ' - ' + item.subtotal + ' birr'
        card.appendChild(p)
    }

    var totalP = document.createElement('p')
    totalP.textContent = 'Total: ' + order.total_price + ' birr'
    card.appendChild(totalP)
    
    localStorage.setItem('currentOrder', JSON.stringify(order))
}

function restoreOrderCard() {
    var savedOrder = localStorage.getItem('currentOrder')
    if (savedOrder) {
        var order = JSON.parse(savedOrder)
        showCurrentOrder(order)
    }
}

async function confirmOrder() {
    if (orderCount === 0) {
        alert("You haven't ordered anything yet.")
        return
    }

    var orders = []
    for (var name in orderItems) {
        orders.push({ 'name': name, 'quantity': orderItems[name] })
    }

    var response = await fetch('/order', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        },
        body: JSON.stringify(orders)
    })

    var data = await response.json()

    if (!response.ok) {
        alert('Order failed: ' + (data.error || 'something went wrong'))
        return
    }

    alert('Your Order has been sent! Total: ' + data.order.total_price + ' birr')

    showCurrentOrder(data.order)

    orderCount = 0
    TotalPrice = 0
    orderItems = {}
    updateSummary()
    saveOrderData()
}

function updateTime() {
    var timeEl = document.getElementById('current-time')
    var now = new Date()
    timeEl.innerText = now.toString().slice(0, 24)
}

function searchfood() {
    var input = document.getElementById('myInput')
    var lower = input.value.toLowerCase()
    var cards = document.getElementsByClassName('food')
    for (var i = 0; i < cards.length; i++) {
        var titleEl = cards[i].getElementsByClassName('food-card')[0]
        var title = titleEl.innerText.toLowerCase()
        cards[i].style.display = title.indexOf(lower) !== -1 ? '' : 'none'
    }
}

async function start() {
    loadOrderData()
    updateSummary()
    restoreOrderCard()
    updateTime()
    setInterval(updateTime, 1000)

    var menuContainer = document.querySelector('.menu-container')
    if (!menuContainer) {
        return
    }

    menuContainer.innerHTML = ''

    try {
        var response = await fetch('/menu')
        var menuData = await response.json()

        for (var title in menuData) {
            var item = menuData[title]
            var card = document.createElement('div')
            card.className = 'food'
            card.innerHTML = [
                '<img src="' + item.image + '" alt="' + title + '">',
                '<h3 class="food-card">' + title + '</h3>',
                '<p>' + item.description + '</p>',
                '<p class="price">' + item.price + ' birr</p>',
                '<button class="order-button" onclick="handleOrderClick(event)">Add to Order</button>'
            ].join('')
            menuContainer.appendChild(card)
        }
    } catch (error) {
        menuContainer.innerHTML = '<p>Unable to load menu right now.</p>'
    }
}

window.addEventListener('DOMContentLoaded', start)
