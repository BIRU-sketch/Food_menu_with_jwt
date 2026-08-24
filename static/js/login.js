async function submit() {
    let name=document.getElementById('username').value
    let password=document.getElementById('password').value
    let response = await fetch("/login",{
        method:'POST',
        headers:{
            "Content-Type":"application/json",
            "Accept":"application/json"
        },
        body:JSON.stringify({"name":name,"password":password}),

    })
    if (!response.ok){
        p=document.getElementById("errormsg")
        p.textContent="Invalid Credential/s"
    }
    else{
        let data=await response.json()
        let token= data.token
        localStorage.setItem('token', token)
        window.location.href = "/admin/orders"
    }


}