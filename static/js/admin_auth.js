function redirectWhenTokenExpires() {
    let token = localStorage.getItem('token')

    if (!token) {
        window.location.href = '/login'
        return
    }

    try {
        let encodedPayload = token.split('.')[1]
        let payload = JSON.parse(atob(encodedPayload.replace(/-/g, '+').replace(/_/g, '/')))
        let remainingTime = payload.exp * 1000 - Date.now()

        if (remainingTime <= 0) {
            localStorage.removeItem('token')
            window.location.href = '/login'
            return
        }
        setTimeout(function () {
            localStorage.removeItem('token')
            window.location.href = '/login'
        }, remainingTime)
    } catch (error) {
        localStorage.removeItem('token')
        window.location.href = '/login'
    }
}
redirectWhenTokenExpires();