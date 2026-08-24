document.addEventListener('DOMContentLoaded',async ()=>{
    let response = await fetch("/admin/orders",{
        method:'GET',
        headers:{
            'Authorization':localStorage.getItem('token')
        }
    })

    if (response.status === 401) {
        localStorage.removeItem('token')
        window.location.href = '/login'
    }
})